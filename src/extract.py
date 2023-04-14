from pprint import pprint

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

# Define the Verilog grammar
verilog_grammar = Grammar(
    r"""
    Instance      = Name ParameterList? Name PortList ";"

    ParameterList = "#" "(" Parameter+ ")"
    Parameter     = Name ("," / "")

    PortList      = "(" Port+ ")"
    Port          = ws "." Name "(" Name ")" ("," / "") ws

    Name          = ws ~"\w+" ws
    ws            = ~"\s*"
    """
)


class VerilogVisitor(NodeVisitor):
    def visit_Instance(self, node, visited_children):
        module_name, parameters, _, ports, _ = visited_children
        parameters = parameters[0] if isinstance(parameters, list) else None

        return {
            "module_name": module_name,
            "parameters": parameters,
            "port_names": ports,
        }

    def visit_ParameterList(self, node, visited_children):
        return visited_children[2]

    def visit_Parameter(self, node, visited_children):
        return visited_children[0]

    def visit_PortList(self, node, visited_children):
        return visited_children[1]

    def visit_Port(self, node, visited_children):
        return visited_children[2]

    def visit_Name(self, node, visited_children):
        return visited_children[1].text

    def generic_visit(self, node, visited_children):
        """The generic visit method."""

        return visited_children or node


def extract_instance(file_path: str) -> dict:
    # Load the Verilog file and preprocess it
    with open(file_path, "r") as f:
        verilog_code = f.read()
        start_index = verilog_code.lower().find("// instance of ")
        assert start_index >= 0, "Error: search string not found"
        verilog_code = verilog_code[start_index:]
        end_index = verilog_code.find(";")
        assert end_index >= 0, "Error: delimiter not found"
        verilog_code = verilog_code[: end_index + 1]
        comment_index = verilog_code.find("\n")
        assert comment_index >= 0, "Error: comment line not found"
        verilog_code = verilog_code[comment_index + 1 :]

    verilog_tree = verilog_grammar.parse(verilog_code)
    verilog_visitor = VerilogVisitor()
    verilog_instance = verilog_visitor.visit(verilog_tree)

    return verilog_instance
