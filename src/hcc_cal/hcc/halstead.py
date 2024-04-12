import javalang
import numpy as np

from hcc_cal.commit import Method


def halstead(method: Method) -> dict[float]:
    operators = []
    operands = []

    for _, node in method.ast:
        if getattr(node, "modifiers", None):
            operators.extend(node.modifiers)
        if getattr(node, "throws", None):
            operators.append("throws")
            operands.extend(node.throws)

        if isinstance(node, javalang.tree.Expression):
            if getattr(node, "operator", None):
                operators.append(node.operator)
            if getattr(node, "prefix_operators", None):
                operators.extend(node.prefix_operators)
            if getattr(node, "postfix_operators", None):
                operators.extend(node.postfix_operators)
            if getattr(node, "qualifier", None):
                operators.append(".")
                operands.append(node.qualifier)

            if isinstance(node, javalang.tree.ArraySelector):
                operators.append("[]")
            elif isinstance(node, javalang.tree.Cast):
                operators.append("()")
                operands.append(node.type.name)
            elif isinstance(node, javalang.tree.Assignment):
                operators.append(node.type)
            elif isinstance(node, javalang.tree.MethodReference):
                operators.append("::")
            elif isinstance(node, javalang.tree.LambdaExpression):
                operators.append("->")
            elif isinstance(node, javalang.tree.ClassReference):
                operators.append(".class")
            elif isinstance(node, javalang.tree.TernaryExpression):
                operators.append("?:")

            elif isinstance(node, javalang.tree.Invocation):
                operators.append("()")

                if getattr(node, "type_arguments", None):
                    operators.append("<>")
                    for type_arg in node.type_arguments:
                        operands.append(type_arg.type)

                if isinstance(
                    node,
                    (
                        javalang.tree.MethodInvocation,
                        javalang.tree.SuperMethodInvocation,
                    ),
                ):
                    operands.append(node.member)
                if isinstance(node, javalang.tree.ExplicitConstructorInvocation):
                    operands.append("this")
                if isinstance(node, javalang.tree.SuperConstructorInvocation):
                    operands.append("super")

            elif isinstance(
                node,
                (javalang.tree.MemberReference, javalang.tree.SuperMemberReference),
            ):
                operands.append(node.member)
            elif isinstance(node, javalang.tree.This):
                operands.append("this")
            elif isinstance(node, javalang.tree.Literal):
                operands.append(node.value)

        if isinstance(node, javalang.tree.Creator):
            operators.append("new")
            operands.append(node.type.name)

        if isinstance(node, javalang.tree.IfStatement):
            if node.then_statement:
                operators.append("if")
            if node.else_statement:
                operators.append("else")
        if isinstance(node, javalang.tree.ForControl):
            operators.append("for")
        if isinstance(node, javalang.tree.EnhancedForControl):
            operators.extend(["for", ":"])
        if isinstance(node, javalang.tree.WhileStatement):
            operators.append("while")
        if isinstance(node, javalang.tree.DoStatement):
            operators.append("do")
        if isinstance(node, javalang.tree.SynchronizedStatement):
            operators.append("synchronized")
        if isinstance(node, javalang.tree.SwitchStatement):
            operators.append("switch")
        if isinstance(node, javalang.tree.SwitchStatementCase):
            if len(node.case) > 0:
                operators.append("case")
            else:
                operators.append("default")
        if isinstance(node, javalang.tree.BreakStatement):
            operators.append("break")
        if isinstance(node, javalang.tree.TryStatement):
            operators.append("try")
            if node.finally_block:
                operators.append("finally")
        if isinstance(node, javalang.tree.CatchClause):
            operators.append("catch")
        if isinstance(node, javalang.tree.CatchClauseParameter):
            operands.append(node.name)
        if isinstance(node, javalang.tree.ThrowStatement):
            operators.append("throw")
        if isinstance(node, javalang.tree.ContinueStatement):
            operators.append("continue")
        if isinstance(node, javalang.tree.AssertStatement):
            operators.append("assert")
        if isinstance(node, javalang.tree.ReturnStatement):
            operators.append("return")
    # Calculate Halstead metrics
    n1 = len(set(operators))  # Number of distinct operators
    n2 = len(set(operands))  # Number of distinct operands
    N1 = len(operators)  # Total number of operators
    N2 = len(operands)  # Total number of operands

    vocabulary = n1 + n2
    length = N1 + N2
    volume = length * np.log2(vocabulary) if vocabulary > 0 else 0
    difficulty = (n1 / 2) * (N2 / n2) if n2 != 0 else 0
    effort = difficulty * volume

    return {
        "vocabulary": vocabulary,
        "length": length,
        "volume": volume,
        "difficulty": difficulty,
        "effort": effort,
    }
