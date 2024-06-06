import numpy as np

from javalang.tokenizer import Identifier
from javalang.tree import (
    SuperConstructorInvocation,
    SuperMethodInvocation,
    MethodInvocation,
    ExplicitConstructorInvocation,
)

from hcc_cal.commit import Method, MethodChangesCommit
from hcc_cal.hcc.cfg import CFG, use_def_graph
from hcc_cal.hcc.halstead import halstead
from hcc_cal.hcc.rii import incorrect_indentation_ratio


class HCCMethodMetrics:
    def __init__(
        self,
        method: Method,
        commit_hash: str,
        checkstyle_path: str,
        xml_path: str,
        checkstyle_cache_dir: str,
    ) -> None:
        self.method = method
        self.cfg = CFG(self.method)
        self.cfg.compute_reaching_definitions()
        self.halstead = halstead(self.method)
        self.commit_hash = commit_hash
        self.checkstyle_path = checkstyle_path
        self.xml_path = xml_path
        self.checkstyle_cache_dir = checkstyle_cache_dir

    @property
    def V(self):
        """
        V: The Halstead’s volume that measures the minimum number of bits needed to represent the change and its context
        """
        return self.halstead["volume"]

    @property
    def ENT(self):
        """
        ENT: The entropy value representing the relative distribution of the terms
        """
        tokens = [token.value for token in self.method.tokens]
        unique_tokens = set(tokens)
        token_count = len(tokens)
        token_entropy = 0
        for token in unique_tokens:
            token_probability = tokens.count(token) / token_count
            token_entropy += token_probability * np.log2(token_probability)
        token_entropy *= -1
        return token_entropy

    @property
    def DD(self):
        """
        DD: The DepDegree value that measures the total number of edges in the data-flow graph
        """
        return use_def_graph(self.cfg).depdegree

    @property
    def ENT_V(self):
        """
        ENT/V: The entropy value representing the relative distribution of the terms per V
        """
        return self.ENT / self.V

    @property
    def DD_V(self):
        """
        DD/V: The DepDegree value that measures the total number of edges in the data-flow graph per V
        """
        return self.DD / self.V

    @property
    def MDNL(self):
        """
        MDNL: The max depth of nesting loop
        """
        return self.cfg.MDNL

    @property
    def NB(self):
        """
        NB: The total number of non-structured branch statements (e.g., continue, break)
        """
        return self.cfg.NB

    @property
    def REC(self):
        """
        REC: The ratio of external calls to total calls
        """
        called_methods = set()
        local_methods = set()
        for _, node in self.method.ast:
            if isinstance(node, MethodInvocation):
                if node.qualifier:
                    called_methods.add(f"{node.qualifier}.{node.member}")
                else:
                    local_methods.add(node.member)
            elif isinstance(node, SuperConstructorInvocation):
                called_methods.add("super")
            elif isinstance(node, SuperMethodInvocation):
                called_methods.add(f"super.{node.member}")
            elif isinstance(node, ExplicitConstructorInvocation):
                local_methods.add("this")
        total = len(local_methods) + len(called_methods)
        if total == 0:
            return 0
        return len(called_methods) / total

    @property
    def NP(self):
        """
        NP: The number of parameters
        """
        return len(self.method.ast.parameters)

    @property
    def RG(self):
        """
        RG: The ratio of global variables to total variables
        """
        return (
            (len(self.cfg.global_variables) / len(self.cfg.variables))
            if len(self.cfg.variables) > 0
            else 0
        )

    @property
    def NTM(self):
        """
        NTM: The number of terms in the line with the most terms
        """
        tokens = [token for token in self.method.tokens]
        tokens_per_line = {}
        for token in tokens:
            if token.position.line not in tokens_per_line:
                tokens_per_line[token.position.line] = []
            tokens_per_line[token.position.line].append(token)
        terms_per_line = np.max([len(tokens) for tokens in tokens_per_line.values()])
        return terms_per_line

    @property
    def TS(self):
        """
        TS: The number of variables that have short names
        """
        except_tokens = ["i", "e"]
        too_shorts = [
            token.value
            for token in self.method.tokens
            if isinstance(token, Identifier)
            and len(token.value) <= 2
            and token.value not in except_tokens
        ]

        return len(set(too_shorts))

    @property
    def RII(self):
        """
        RII: The ratio of warnings for incorrect indentations from CheckStyle to toal lines
        """
        return incorrect_indentation_ratio(
            self.method,
            self.commit_hash,
            cache_dir=self.checkstyle_cache_dir,
            checkstyle_path=self.checkstyle_path,
            xml_path=self.xml_path,
        )


class HCCCommitMetrics:
    def __init__(
        self,
        commit: MethodChangesCommit,
        checkstyle_path="checkstyle.jar",
        xml_path="indentation_config.xml",
        checkstyle_cache_dir="data/cache/checkstyle",
        by="mean",
    ) -> None:
        self.commit = commit
        self.by = by

        self.method_metrics = [
            HCCMethodMetrics(
                method,
                commit.commit_hash,
                checkstyle_path,
                xml_path,
                checkstyle_cache_dir,
            )
            for method in self.commit.methods_after
        ]

    def set_paths(
        self,
        checkstyle_path="checkstyle.jar",
        xml_path="indentation_config.xml",
        checkstyle_cache_dir="data/cache/checkstyle",
    ):
        for metric in self.method_metrics:
            metric.checkstyle_path = checkstyle_path
            metric.xml_path = xml_path
            metric.checkstyle_cache_dir = checkstyle_cache_dir

    def _aggregate(self, metric: str):
        values = [getattr(method, metric) for method in self.method_metrics]
        if self.by == "max":
            return max(values)
        elif self.by == "min":
            return min(values)
        elif self.by == "mean":
            return np.mean(values)
        elif self.by == "median":
            return np.median(values)
        elif self.by == "sum":
            return sum(values)
        else:
            raise ValueError(f"Invalid aggregation method: {self.by}")

    @property
    def all(self):
        return {
            "V": self.V,
            "entropy": self.ENT,
            "DD": self.DD,
            "MDNL": self.MDNL,
            "NB": self.NB,
            "REC": self.REC,
            "NP": self.NP,
            "RG": self.RG,
            "NTM": self.NTM,
            # "RII": self.RII,
            "ENT_V": self.ENT_V,
            "DD_V": self.DD_V,
            "TS": self.TS,
        }

    @property
    def V(self):
        return self._aggregate("V")

    @property
    def ENT(self):
        return self._aggregate("ENT")

    @property
    def DD(self):
        return self._aggregate("DD")

    @property
    def MDNL(self):
        return self._aggregate("MDNL")

    @property
    def NB(self):
        return self._aggregate("NB")

    @property
    def REC(self):
        return self._aggregate("REC")

    @property
    def NP(self):
        return self._aggregate("NP")

    @property
    def RG(self):
        return self._aggregate("RG")

    @property
    def NTM(self):
        return self._aggregate("NTM")

    @property
    def RII(self):
        return self._aggregate("RII")

    @property
    def ENT_V(self):
        return self._aggregate("ENT_V")

    @property
    def DD_V(self):
        return self._aggregate("DD_V")

    @property
    def TS(self):
        return self._aggregate("TS")
