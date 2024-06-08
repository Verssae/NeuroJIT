import uuid
from dataclasses import dataclass
from typing import List, Self, Union, Dict, Set, Tuple

from javalang.ast import Node
from javalang.tree import (
    IfStatement,
    WhileStatement,
    ForStatement,
    ForControl,
    DoStatement,
    TryStatement,
    SwitchStatement,
    BreakStatement,
    ContinueStatement,
    ReturnStatement,
    AssertStatement,
    StatementExpression,
    VariableDeclaration,
    ThrowStatement,
    SynchronizedStatement,
    BlockStatement,
    SwitchStatementCase,
    Expression,
    Assignment,
    FormalParameter,
    MemberReference,
    VariableDeclarator,
    EnhancedForControl,
    CatchClauseParameter,
    BinaryOperation,
    TernaryExpression,
    Cast,
    MethodInvocation,
    ArrayInitializer,
    This,
    SuperMethodInvocation,
)

from neurojit.commit import Method

Statement = Union[Node, str]


class CFGNode:
    def __init__(self, statement: Statement, metadata={}, virtual=False):
        self.statement = statement
        self.metadata = metadata
        self.name = self._name()

        self.parents = set()
        self.children = set()
        self.gen = set()
        self.kill = set()
        self.in_set = set()
        self.out_set = set()
        self.end_node = None
        self.virtual = virtual
        self.uses = set()

    def __repr__(self):
        return self.name

    def _name(self):
        pos = getattr(self.statement, "position", None) or getattr(
            self.statement, "_position", None
        )
        if self.metadata.get("type", ""):
            return f"{self.metadata.get('type', '')}_{uuid.uuid4().hex[:4]}" + (
                f"_{pos.line}" if pos else ""
            )
        elif isinstance(self.statement, str):
            return f"{self.statement}_{uuid.uuid4().hex[:4]}"
        else:
            return f"{type(self.statement).__name__}_{uuid.uuid4().hex[:4]}" + (
                f"_{pos.line}" if pos else ""
            )

    @property
    def label(self):
        if isinstance(self.statement, Node) and getattr(self.statement, "label", None):
            return self.statement.label
        return None


@dataclass
class Variable:
    name: str
    assigner: CFGNode
    global_var: bool = False

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name and self.assigner == other.assigner

    def __repr__(self):
        return f"{self.name}<-{self.assigner}"


class CFG:
    def __init__(self, method: Method = None):
        self.nodes: Dict[str, CFGNode] = {}
        self.definitions = {}
        self.unresolved_breaks = {}  # label: [break_nodes ]
        self.unresolved_continues = {}  # label: [continue_nodes]
        self.loop_stack = []
        self.exception_stack = []
        self.labels = {}
        self.method = method
        self.metrics = {}

        if method:
            self.build_cfg(method)

    def add_node(self, cfg_node: CFGNode) -> Self:
        self.nodes[cfg_node.name] = cfg_node
        return self

    def add_edge(self, parent: CFGNode, child: CFGNode) -> Self:
        if parent == child:
            return self
        parent.children.add(child)
        child.parents.add(parent)
        return self

    @property
    def edges(self) -> Set[Tuple[CFGNode, CFGNode]]:
        edges = set()
        for node in self.nodes.values():
            for child in node.children:
                edges.add((node, child))
            for parent in node.parents:
                edges.add((parent, node))
        return edges

    @property
    def global_variables(self) -> Set[str]:
        return set([var.name for var in self.definitions.values() if var.global_var])

    @property
    def variables(self) -> Set[str]:
        return set(self.definitions.keys())

    @property
    def local_variables(self) -> Set[str]:
        return self.variables - self.global_variables

    def compute_gen_kill(self, node: CFGNode):
        used = set()
        defined = set()
        self_def_used = set()

        def find_variables(expression: Node, where="use"):
            if isinstance(expression, MemberReference):
                variable = expression.member
                if getattr(expression, "qualifier", None):
                    variable = expression.qualifier

                if {"++", "--"} & (
                    set(expression.prefix_operators or [])
                    | set(expression.postfix_operators or [])
                ):
                    self_def_used.add(variable)

                if where == "both":
                    defined.add(variable)
                    used.add(variable)
                elif where == "def":
                    defined.add(variable)
                else:
                    used.add(variable)

            elif isinstance(expression, BinaryOperation):
                find_variables(expression.operandl, where)
                find_variables(expression.operandr, where)
            elif isinstance(expression, TernaryExpression):
                find_variables(expression.condition, where)
                if expression.if_true:
                    find_variables(expression.if_true, where)
                if expression.if_false:
                    find_variables(expression.if_false, where)
            elif isinstance(expression, Cast):
                find_variables(expression.expression, where)
            elif isinstance(expression, Assignment):
                if expression.type in ["+=", "-="]:
                    find_variables(expression.expressionl, where="both")
                else:
                    find_variables(expression.expressionl, where="def")
                find_variables(expression.value, where="use")
            elif isinstance(expression, VariableDeclaration):
                for declarator in expression.declarators:
                    find_variables(declarator, where="def")
            elif isinstance(expression, VariableDeclarator):
                if expression.name:
                    defined.add(expression.name)

                if expression.initializer:
                    find_variables(expression.initializer)
            elif isinstance(expression, FormalParameter):
                defined.add(expression.name)
                if expression.varargs:
                    defined.add(expression.varargs)
            elif isinstance(expression, EnhancedForControl):
                for declarator in expression.var.declarators:
                    find_variables(declarator, where="def")
                find_variables(expression.iterable, where="use")
            elif isinstance(expression, CatchClauseParameter):
                defined.add(expression.name)

            elif getattr(expression, "initializer", None):
                find_variables(expression.initializer, where="use")
            elif isinstance(expression, ArrayInitializer):
                for init in expression.initializers:
                    find_variables(init, where="use")
            elif isinstance(expression, MethodInvocation):
                if expression.qualifier and expression.qualifier != "this":
                    used.add(expression.qualifier)
                for arg in expression.arguments:
                    find_variables(arg, where="use")
            elif isinstance(expression, SuperMethodInvocation):
                if expression.qualifier and expression.qualifier == "super":
                    used.add(expression.qualifier)
                for arg in expression.arguments:
                    find_variables(arg, where="use")
            elif isinstance(expression, This):
                for selector in expression.selectors:
                    find_variables(selector, where=where)
            elif getattr(expression, "arguments", None):
                for arg in expression.arguments:
                    find_variables(arg, where="use")
            else:
                pass

        if isinstance(node.statement, str) or node.virtual:
            return

        find_variables(node.statement)

        for name in used:
            if name not in self.definitions:
                # It was not defined in this method (global variable)
                self.definitions[name] = Variable(name, None, global_var=True)
            node.uses.add(self.definitions[name])

        for name in defined:
            if name in self.definitions:
                # Kill the previous definition
                node.kill.add(self.definitions[name])
                self.definitions[name].assigner = node
            else:
                # It is a new definition
                self.definitions[name] = Variable(name, node)
            node.gen.add(self.definitions[name])

        for name in self_def_used:
            if name in self.definitions:
                node.kill.add(self.definitions[name])
                self.definitions[name].assigner = node
            else:
                self.definitions[name] = Variable(name, node)
            node.gen.add(self.definitions[name])
            node.uses.add(self.definitions[name])

    def build_cfg(self, method: Method):
        # Add entry and exit nodes
        self.entry_node = CFGNode("ENTRY", virtual=True)
        self.exit_node = CFGNode("EXIT", virtual=True)
        self.add_node(self.entry_node).add_node(self.exit_node)
        self.exception_stack.append(self.exit_node)

        for parameter in method.ast.parameters:
            parameter_node = CFGNode(parameter, {"type": "PARAM"})
            self.add_node(parameter_node).add_edge(parameter_node, self.entry_node)

        last_node = self._control_flow(self.entry_node, method.ast.body)
        if last_node != self.exit_node:
            self.add_edge(last_node, self.exit_node)

        # Resolve any unsolved breaks and continues
        if self.unresolved_breaks:
            self._resolve_breaks()
        if self.unresolved_continues:
            self._resolve_continues()

        self.exception_stack.pop()

    def _process_block(self, parent: CFGNode, block: List[Node]) -> CFGNode:
        last_node = parent
        for statement in block:
            current_node = self._control_flow(last_node, statement)
            last_node = current_node
        return last_node

    def _register_labels(self):
        for node in self.nodes.values():
            if node.label:
                self.labels[node.label] = node

    def _control_flow(self, parent: CFGNode, statement: Node) -> CFGNode:
        if self.loop_stack:
            max_depth = max(self.metrics.get("max_depth_loop", 0), len(self.loop_stack))
            self.metrics["max_depth_loop"] = max_depth

        if isinstance(statement, (list, tuple)):
            return self._process_block(parent, statement)
        elif isinstance(statement, (BlockStatement, SwitchStatementCase)):
            if getattr(statement, "label", None):
                block_node = CFGNode(statement, {"type": "BLOCK"})
                self.add_node(block_node).add_edge(parent, block_node)
                self.labels[statement.label] = block_node
                return self._process_block(block_node, statement.statements)
            return self._process_block(parent, statement.statements)
        elif isinstance(statement, IfStatement):
            return self._process_if(parent, statement)
        elif isinstance(statement, WhileStatement):
            return self._process_while(parent, statement)
        elif isinstance(statement, ForStatement):
            return self._process_for(parent, statement)
        elif isinstance(statement, DoStatement):
            return self._process_do(parent, statement)
        elif isinstance(statement, TryStatement):
            return self._process_try(parent, statement)
        elif isinstance(statement, SwitchStatement):
            return self._process_switch(parent, statement)

        elif isinstance(statement, BreakStatement):
            return self._process_break(parent, statement)
        elif isinstance(statement, ContinueStatement):
            return self._process_continue(parent, statement)
        elif isinstance(statement, ReturnStatement):
            return self._process_return(parent, statement)
        elif isinstance(statement, AssertStatement):
            return self._process_assert(parent, statement)
        elif isinstance(statement, SynchronizedStatement):
            return self._process_synchronized(parent, statement)
        elif isinstance(statement, ThrowStatement):
            return self._process_throw(parent, statement)
        elif isinstance(statement, (StatementExpression)):
            return self._process_expression(parent, statement.expression)
        elif isinstance(statement, (VariableDeclaration, Expression, Statement)):
            return self._process_expression(parent, statement)
        else:
            return parent

    def _process_expression(
        self, parent: CFGNode, statement: Union[VariableDeclaration, Expression]
    ) -> CFGNode:
        # Create a node for the statement
        statement_node = CFGNode(statement)
        self.add_node(statement_node).add_edge(parent, statement_node)
        return statement_node

    def _process_if(self, parent: CFGNode, if_statement: IfStatement) -> CFGNode:
        if_node = CFGNode(if_statement, virtual=True, metadata={"type": "IF"})
        self.add_node(if_node).add_edge(parent, if_node)
        end_node = CFGNode("END_IF", virtual=True)
        self.add_node(end_node)
        # Create a node for the if condition
        condition_node = CFGNode(if_statement.condition, {"type": "IF_COND"})
        self.add_node(condition_node).add_edge(if_node, condition_node)
        self.add_edge(condition_node, end_node)

        # Process the then block
        then_statement = if_statement.then_statement
        last_then_node = self._control_flow(condition_node, then_statement)

        # Process the else block if it exists
        last_else_node = None
        if if_statement.else_statement:
            else_statement = if_statement.else_statement
            last_else_node = self._control_flow(condition_node, else_statement)

        # Create a join node for after the if-else structure

        self.add_edge(last_then_node, end_node)
        if last_else_node:
            self.add_edge(last_else_node, end_node)

        return end_node

    def _process_while(
        self, parent: CFGNode, while_statement: WhileStatement
    ) -> CFGNode:
        while_node = CFGNode(while_statement, virtual=True, metadata={"type": "WHILE"})
        self.add_node(while_node).add_edge(parent, while_node)

        # Create a node for the while condition
        condition_node = CFGNode(while_statement.condition, {"type": "WHILE_COND"})
        end_node = CFGNode("END_WHILE", virtual=True)
        condition_node.end_node = end_node

        self.add_node(condition_node)
        self.add_node(end_node)

        self.add_edge(while_node, condition_node)
        self.add_edge(condition_node, end_node)

        # Process the body of the while statement
        self.loop_stack.append(condition_node)
        last_body_node = self._control_flow(condition_node, while_statement.body)

        self.add_edge(last_body_node, condition_node)
        self.add_edge(last_body_node, end_node)

        self.loop_stack.pop()

        return end_node

    def _process_do(self, parent: CFGNode, do_statement: DoStatement) -> CFGNode:
        # Create a join node for after the do-while loop
        block_node = CFGNode(do_statement, virtual=True, metadata={"type": "DO"})
        condition_node = CFGNode(do_statement.condition, {"type": "DO_COND"})
        end_node = CFGNode("END_DO", virtual=True)
        condition_node.end_node = end_node

        self.add_node(block_node).add_node(condition_node).add_node(end_node)
        self.add_edge(parent, block_node)

        self.loop_stack.append(condition_node)
        last_body_node = self._control_flow(block_node, do_statement.body)

        self.add_edge(last_body_node, condition_node)

        self.add_edge(condition_node, block_node)

        self.add_edge(condition_node, end_node)

        self.loop_stack.pop()

        return end_node

    def _process_for(self, parent: CFGNode, for_statement: ForStatement) -> CFGNode:
        for_node = CFGNode(for_statement, virtual=True, metadata={"type": "FOR"})
        self.add_node(for_node).add_edge(parent, for_node)

        # Check if this is a for loop or a for-each loop
        if isinstance(for_statement.control, ForControl):
            for_init = CFGNode("FOR_INIT", virtual=True)
            self.add_node(for_init).add_edge(for_node, for_init)

            if for_statement.control.init:
                last_for_init = self._control_flow(for_init, for_statement.control.init)
            else:
                last_for_init = for_init

            for_update = CFGNode("FOR_UPDATE", virtual=True)
            self.add_node(for_update)

            if for_statement.control.update:
                last_for_update = self._control_flow(
                    for_update, for_statement.control.update
                )
            else:
                last_for_update = for_update

            end_node = CFGNode("END_FOR", virtual=True)
            self.add_node(end_node)

            if for_statement.control.condition:
                for_condition = CFGNode(
                    for_statement.control.condition, {"type": "FOR_COND"}
                )
                for_condition.end_node = end_node
                self.add_node(for_condition)
                self.add_edge(for_node, last_for_init).add_edge(
                    last_for_init, for_condition
                )

                # Process the condition body
                self.add_edge(for_condition, end_node)
            else:
                for_condition = CFGNode("FOR_COND", virtual=True)
                for_condition.end_node = end_node
                self.add_node(for_condition)
                self.add_edge(for_node, last_for_init).add_edge(
                    last_for_init, for_condition
                )

            self.loop_stack.append(for_condition)

            last_body_node = self._control_flow(for_condition, for_statement.body)

            self.add_edge(last_body_node, for_update)
            self.add_edge(last_body_node, end_node)
            self.add_edge(last_for_update, for_condition)

            self.loop_stack.pop()
            return end_node

        elif isinstance(for_statement.control, EnhancedForControl):
            for_each = CFGNode(for_statement.control, {"type": "FOR_EACH"})
            end_node = CFGNode("END_FOR", virtual=True)
            for_each.end_node = end_node

            self.add_node(for_each).add_node(end_node)
            self.add_edge(for_node, for_each)

            self.loop_stack.append(for_each)
            last_body_node = self._control_flow(for_each, for_statement.body)

            self.add_edge(last_body_node, for_each)
            self.add_edge(for_each, end_node)

            self.loop_stack.pop()
            return end_node
        else:
            raise ValueError(
                f"Unsupported for statement control: {type(for_statement.control)}"
            )

    def _process_break(
        self, parent: CFGNode, break_statement: BreakStatement
    ) -> CFGNode:
        break_node = CFGNode(break_statement, virtual=True, metadata={"type": "BREAK"})
        self.add_node(break_node)
        self.add_edge(parent, break_node)

        # 'goto' 라벨이 있는 경우
        if getattr(break_statement, "goto", None):
            self._register_labels()
            label = break_statement.goto
            label_node = self.labels.get(label, None)
            if label_node:
                self.add_edge(break_node, label_node)
                return label_node
            else:
                # Store the unresolved break for later resolution
                if label not in self.unresolved_breaks:
                    self.unresolved_breaks[label] = []
                self.unresolved_breaks[label].append(break_node)
                return break_node

        # 'goto' 라벨이 없는 경우
        else:
            # Find the loop start node
            loop_start_node = self.loop_stack[-1]
            if loop_start_node.end_node is not None:
                self.add_edge(break_node, loop_start_node.end_node)
                if loop_start_node.end_node.name.startswith("END_SWITCH"):
                    if "switch_branches" not in self.metrics:
                        self.metrics["switch_branches"] = []
                    self.metrics["switch_branches"].append(break_statement)
                return loop_start_node.end_node
            else:
                self.add_edge(break_node, loop_start_node)
                return loop_start_node

    def _resolve_breaks(self):
        self._register_labels()
        for label, break_nodes in self.unresolved_breaks.items():
            label_node = self.labels.get(label, None)
            if not label_node:
                raise ValueError(f"Label '{label}' not found for unresolved breaks")

            for break_node in break_nodes:
                self.add_edge(break_node, label_node)

    def _process_continue(
        self, parent: CFGNode, continue_statement: ContinueStatement
    ) -> CFGNode:
        continue_node = CFGNode(
            continue_statement, virtual=True, metadata={"type": "CONTINUE"}
        )
        self.add_node(continue_node)
        self.add_edge(parent, continue_node)

        # 'goto' 라벨이 있는 경우
        if getattr(continue_statement, "goto", None):
            self._register_labels()
            label = continue_statement.goto
            label_node = self.labels.get(label, None)
            if label_node:
                self.add_edge(continue_node, label_node)
                return label_node
            else:
                # Store the unresolved break for later resolution
                if label not in self.unresolved_continues:
                    self.unresolved_continues[label] = []
                self.unresolved_continues[label].append(continue_node)
                return continue_node

        # 'goto' 라벨이 없는 경우
        else:
            # Find the loop start node
            loop_start_node = self.loop_stack[-1]
            self.add_edge(continue_node, loop_start_node)
            return loop_start_node

    def _resolve_continues(self):
        self._register_labels()
        for label, continue_nodes in self.unresolved_continues.items():
            loop_start_node = self.labels.get(label, None)
            if not loop_start_node:
                raise ValueError(
                    f"Loop start for label '{label}' not found for unresolved continues"
                )

            for continue_node in continue_nodes:
                self.add_edge(continue_node, loop_start_node)

    def _process_return(
        self, parent: CFGNode, return_statement: ReturnStatement
    ) -> CFGNode:
        if return_statement.expression:
            return_node = CFGNode(return_statement.expression, {"type": "RETURN"})
        else:
            return_node = CFGNode(return_statement, virtual=True)
        self.add_node(return_node).add_edge(parent, return_node)

        # if the return statement is in try-finally block, the finally block captures the return statement
        end_node = (
            self.exception_stack[-1]
            if self.exception_stack[-1].metadata.get("type", "") == "FIN"
            else self.exit_node
        )
        self.add_edge(return_node, end_node)

        return return_node

    # when assert statement is executed, it is assumed that the program is terminated.
    def _process_assert(
        self, parent: CFGNode, assert_statement: AssertStatement
    ) -> CFGNode:
        assert_node = CFGNode(
            assert_statement, virtual=True, metadata={"type": "ASSERT"}
        )
        self.add_node(assert_node).add_edge(parent, assert_node)

        end_node = CFGNode("END_ASSERT", virtual=True)
        self.add_node(end_node)

        condition_node = CFGNode(assert_statement.condition, {"type": "ASSERT_COND"})
        self.add_node(condition_node).add_edge(assert_node, condition_node)
        self.add_edge(condition_node, end_node)

        if assert_statement.value:
            value_node = CFGNode(assert_statement.value)
            self.add_node(value_node).add_edge(condition_node, value_node)
            self.add_edge(value_node, end_node)

        # if the assert statement is in try-finally block, the finally block captures the assert statement
        if (
            self.exception_stack
            and self.exception_stack[-1].metadata.get("type", "") == "FIN"
        ):
            self.add_edge(end_node, self.exception_stack[-1])
        self.add_edge(end_node, self.exit_node)

        return end_node

    # assume that when an exception is thrown in try block, we consider the throw statement as the last statement in the try block
    def _process_try(self, parent: CFGNode, try_statement: TryStatement) -> CFGNode:
        try_node = CFGNode(try_statement, virtual=True, metadata={"type": "TRY"})
        self.add_node(try_node).add_edge(parent, try_node)

        if try_statement.resources:
            last_resource_node = try_node
            for resource in try_statement.resources:
                resource_node = CFGNode(resource, {"type": "RESOURCE"})
                self.add_node(resource_node).add_edge(last_resource_node, resource_node)
                last_resource_node = resource_node
            last_try_node = last_resource_node
        else:
            last_try_node = try_node

        if try_statement.finally_block:
            finally_node = CFGNode(
                try_statement.finally_block, {"type": "FIN"}, virtual=True
            )
            self.add_node(finally_node)

            # Process the body of the try block
            self.exception_stack.append(finally_node)
            last_try_block = self._control_flow(last_try_node, try_statement.block)
            self.exception_stack.pop()

            self.add_edge(last_try_block, finally_node)
            last_finally_node = self._control_flow(
                finally_node, try_statement.finally_block
            )
        else:
            finally_node = CFGNode("END_TRY", virtual=True)
            self.add_node(finally_node)
            # Process the body of the try block
            self.exception_stack.append(finally_node)
            last_try_block = self._control_flow(last_try_node, try_statement.block)
            self.exception_stack.pop()
            # Create a join node for after the try-catch-finally block

            self.add_edge(last_try_block, finally_node)
            last_finally_node = finally_node

        # Process each catch block
        if try_statement.catches:
            for catch_clause in try_statement.catches:
                catch_node = CFGNode(catch_clause.parameter)
                self.add_node(catch_node).add_edge(last_try_node, catch_node)

                # Process the body of the catch block
                last_catch_node = self._control_flow(catch_node, catch_clause.block)

                # Edge from catch block to join node
                self.add_edge(last_catch_node, finally_node)

        return last_finally_node

    def _process_throw(
        self, parent: CFGNode, throw_statement: ThrowStatement
    ) -> CFGNode:
        throw_node = CFGNode(throw_statement.expression, {"type": "THROW"})
        self.add_node(throw_node).add_edge(parent, throw_node)
        if self.exception_stack:
            self.add_edge(throw_node, self.exception_stack[-1])
            return self.exception_stack[-1]
        else:
            self.add_edge(throw_node, self.exit_node)
            return self.exit_node

    def _process_switch(
        self, parent: CFGNode, switch_statement: SwitchStatement
    ) -> CFGNode:
        # Create a node for the switch statement
        switch_node = CFGNode(switch_statement, {"type": "SWITCH"}, virtual=True)
        self.add_node(switch_node).add_edge(parent, switch_node)
        switch_expression = CFGNode(switch_statement.expression)
        self.add_node(switch_expression).add_edge(switch_node, switch_expression)

        # Process the switch expression
        last_switch_node = self._control_flow(
            switch_expression, switch_statement.expression
        )

        # Create a join node for after the switch statement
        end_node = CFGNode("END_SWITCH")
        self.add_node(end_node).add_edge(last_switch_node, end_node)
        switch_node.end_node = end_node

        # Process each case clause
        last_case_node = None
        for case_clause in switch_statement.cases:
            if case_clause.case:
                case_node = CFGNode(case_clause.case, {"type": "CASE"}, virtual=True)
            else:
                case_node = CFGNode(case_clause, {"type": "DEFAULT"}, virtual=True)

            self.add_node(case_node)
            if last_case_node:
                self.add_edge(last_case_node, case_node)
            self.add_edge(last_switch_node, case_node)

            # Process the body of the case clause

            self.loop_stack.append(switch_expression)
            last_case_node = self._control_flow(case_node, case_clause.statements)
            self.loop_stack.pop()

            # Connect the last node of each case clause to the join node if not already connected
            if last_case_node != end_node:
                self.add_edge(last_case_node, end_node)
            else:
                last_case_node = None

        return end_node

    def _process_synchronized(
        self, parent: CFGNode, synchronized_statement: SynchronizedStatement
    ) -> CFGNode:
        # Create a node for the synchronized statement
        synchronized_node = CFGNode(synchronized_statement.lock, {"type": "SYNC"})
        self.add_node(synchronized_node).add_edge(parent, synchronized_node)

        # Process the body of the synchronized statement
        last_synchronized_node = self._control_flow(
            synchronized_node, synchronized_statement.block
        )
        return last_synchronized_node

    def __repr__(self):
        return f"CFG({len(self.nodes)} nodes)"

    def compute_reaching_definitions(self):
        """
        Compute the reaching definitions for each node in the CFG.
        """
        # 초기화
        for node in self.nodes.values():
            # if node.virtual:
            #     continue
            self.compute_gen_kill(node)
            node.in_set.clear()
            node.out_set.clear()

        self.add_global_variable_nodes()

        # 정의가 변하지 않을 때까지 반복
        changed = True
        while changed:
            changed = False
            for node in self.nodes.values():
                old_out = node.out_set.copy()

                # in_set 계산
                node.in_set = set().union(*[parent.out_set for parent in node.parents])

                # out_set 계산
                node.out_set = (node.in_set - node.kill) | node.gen

                if node.out_set != old_out:
                    changed = True

    def add_global_variable_nodes(self):
        for var_name in self.definitions:
            if self.definitions[var_name].global_var:
                var_node = CFGNode(f"G_{var_name}")
                self.add_node(var_node)
                self.add_edge(var_node, self.entry_node)
                self.definitions[var_name].assigner = var_node
                self.entry_node.gen.add(self.definitions[var_name])

    def non_structured_branches(self):
        switch_breaks = self.metrics.get("switch_branches", [])
        branches = []
        for path, node in self.method.ast:
            if isinstance(node, BreakStatement) and node not in switch_breaks:
                branches.append(node)
            elif isinstance(node, ContinueStatement):
                branches.append(node)
        return branches

    @property
    def NB(self):
        return len(self.non_structured_branches())

    @property
    def MDNL(self):
        return self.metrics.get("max_depth_loop", 0)


class UseDefNode:
    def __init__(self, cfgn: CFGNode) -> None:
        self.uses = set()  # predecessors
        self.defs = set()  # successors
        self.name = cfgn.name
        self.cfgn = cfgn

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, UseDefNode):
            return False
        return self.name == o.name


class UseDefGraph:
    def __init__(self) -> None:
        self.nodes = {}
        self.edges = set()

    def add_node(self, node: UseDefNode):
        self.nodes[node.name] = node
        return self

    def add_edge(self, use: UseDefNode, defn: UseDefNode):
        self.edges.add((use, defn))
        use.defs.add(defn)
        defn.uses.add(use)
        return self

    def __repr__(self) -> str:
        return f"UseDefGraph({len(self.nodes)} nodes, {len(self.edges)} edges)"

    @property
    def depdegree(self):
        return len(self.edges)


def use_def_graph(cfg):
    udg = UseDefGraph()
    for node in cfg.nodes.values():
        if node.in_set & node.uses:
            for variable in node.in_set & node.uses:
                udg.add_edge(UseDefNode(variable.assigner), UseDefNode(node))

    return udg
