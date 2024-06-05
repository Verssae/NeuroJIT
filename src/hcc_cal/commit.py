from dataclasses import dataclass
from itertools import zip_longest
import pickle
import re
from typing import Union
from git import Repo
from javalang.parser import JavaSyntaxError
from javalang.parse import parse
from typing import Set, Optional
from pathlib import Path
from pydriller.domain.commit import Commit, ModificationType
from pydriller import Git
import javalang
from javalang.tree import (
    ClassDeclaration,
    MethodDeclaration,
    ConstructorDeclaration,
)

class Method:
    def __init__(self, ast: javalang.ast.Node, code: str, signature: str):
        self.ast = ast
        self.code = code
        self.documentation = self.ast.documentation
        self.start_line, self.end_line = self._get_position()
        self.signature = signature
        self.added_lines = set()
        self.deleted_lines = set()

    def __eq__(self, __value: object) -> bool:
        if not hasattr(__value, "signature"):
            return False
        return self.signature == __value.signature

    def __hash__(self) -> int:
        return hash(self.signature)

    def __repr__(self) -> str:
        return self.signature

    @property
    def position(self):
        return (self.start_line, self.end_line)

    @property
    def nested_level(self):
        return len(self.signature.split("::"))

    def _get_position(self):
        start_line = self.ast.position.line
        end_line = self.ast.position.line

        if self.ast.annotations:
            line = min(
                [annotation._position.line for annotation in self.ast.annotations]
            )
            if line < start_line:
                start_line = line

        if self.ast.documentation:
            length = len(self.ast.documentation.split("\n"))
            maybe_start_line = start_line - length
            valid = True
            tokens = javalang.tokenizer.tokenize(self.code)
            for token in tokens:
                if token.position.line == maybe_start_line:
                    valid = False
                    break
                elif token.position.line > start_line:
                    break
            if valid:
                start_line = maybe_start_line

        for path, node in self.ast:
            if hasattr(node, "position") and node.position:
                line = node.position.line
            elif hasattr(node, "_position") and node._position:
                line = node._position.line
            else:
                continue
            if line > end_line:
                end_line = line

        tokens = javalang.tokenizer.tokenize(self.code)
        smallest_column = 1000
        for token in tokens:
            if token.position.line == self.ast.position.line:
                if smallest_column > token.position.column:
                    smallest_column = token.position.column
            if token.position.line > end_line:
                if token.value == "}" and token.position.column >= smallest_column:
                    end_line = token.position.line
                else:
                    break

        return start_line, end_line

    def contains(self, line, type):
        if self.ast.position.line <= line <= self.end_line:
            if type == "ADD":
                self.added_lines.add(line)
            elif type == "DELETE":
                self.deleted_lines.add(line)
            return True
        else:
            return False

    @property
    def snippet(self):
        lines = self.code.split("\n")
        return "\n".join(lines[self.start_line - 1 : self.end_line])

    def line_numbers_col(self, show_after: bool = True) -> str:
        lines = self.code.split("\n")
        if show_after:
            return "\n".join(
                [
                    f"{i+self.start_line:4} {'+' if i+self.start_line in self.added_lines else ' '}"
                    for i, line in enumerate(lines[self.start_line - 1 : self.end_line])
                ]
            )
        else:
            return "\n".join(
                [
                    f"{i+self.start_line:4} {'-' if i+self.start_line in self.deleted_lines else ' '}"
                    for i, line in enumerate(lines[self.start_line - 1 : self.end_line])
                ]
            )
    
    def line_numbered_snippet(self, show_after: bool = True) -> str:
        lines = self.code.split("\n")
        if show_after:
            return "\n".join(
                [
                    f"{i+self.start_line:4} |{'+' if i+self.start_line in self.added_lines else ' '} {line}"
                    for i, line in enumerate(lines[self.start_line - 1 : self.end_line])
                ]
            )
        else:
            return "\n".join(
                [
                    f"{i+self.start_line:4} |{'-' if i+self.start_line in self.deleted_lines else ' '} {line}"
                    for i, line in enumerate(lines[self.start_line - 1 : self.end_line])
                ]
            )

    @property
    def tokens(self):
        all_tokens = javalang.tokenizer.tokenize(self.code)
        tokens = []
        for token in all_tokens:
            if self.start_line <= token.position.line <= self.end_line:
                tokens.append(token)

        return tokens

    @property
    def loc(self):
        return self.end_line - self.start_line + 1

    @classmethod
    def from_file(cls, code):
        tree = javalang.parse.parse(code)
        for path, node in tree:
            if isinstance(node, (MethodDeclaration, ConstructorDeclaration)):
                if not node.body:
                    continue
                signature = cls._generate_full_signature(path, node)
                yield cls(node, code, signature)

    @staticmethod
    def _generate_full_signature(path, node) -> str:
        names = []
        for p in path:
            if isinstance(p, ClassDeclaration):
                names.append(p.name)
            elif isinstance(p, (MethodDeclaration, ConstructorDeclaration)):
                # 메서드나 생성자의 파라미터 타입을 가져와서 시그니처를 생성합니다.
                param_types = [param.type.name for param in p.parameters]
                names.append(f'{p.name}({",".join(param_types)})')

        # 마지막 노드(현재 메서드 또는 생성자)의 시그니처를 추가합니다.
        if isinstance(node, (MethodDeclaration, ConstructorDeclaration)):
            param_types = [param.type.name for param in node.parameters]
            names.append(f'{node.name}({",".join(param_types)})')
        # 계층 구조를 "::"로 연결하여 전체 시그니처를 반환합니다.
        return "::".join(names)



@dataclass
class MethodChangesCommit:
    repo: str
    commit_hash: str
    methods_before: Set[Method]
    methods_after: Set[Method] 


class Mining:
    def __init__(self, ignore_comments: bool = True) -> None:
        self.ignore_comments = ignore_comments

    def only_method_changes(
        self,
        repo: str,
        commit_hash: str,
    ) -> Optional[MethodChangesCommit]:
        commit_object = commit_from(repo, commit_hash)
        if not isinstance(commit_object, Commit):
            return None

        changed_java_files = [
            f for f in commit_object.modified_files if f.filename.endswith(".java")
        ]
        # Trivial case: no java files were changed
        if len(changed_java_files) == 0:
            return None

        method_changes_commit = MethodChangesCommit(repo, commit_hash, set(), set())
        # We consider only commits that change methods not added , deleted or renamed
        for f in changed_java_files:
            # Only modified files are considered
            if f.change_type != ModificationType.MODIFY:
                return None

            if self._syntax_error(f.source_code) or self._syntax_error(
                f.source_code_before
            ):
                return None

            added_lines = set([line[0] for line in f.diff_parsed["added"]])
            deleted_lines = set([line[0] for line in f.diff_parsed["deleted"]])

            for before, after in zip_longest(
                Method.from_file(f.source_code_before), Method.from_file(f.source_code)
            ):
                if before != after:
                    return None

                added_lines_in_method = {
                    line for line in added_lines if after.contains(line, "ADD")
                }
                deleted_lines_in_method = {
                    line for line in deleted_lines if before.contains(line, "DELETE")
                }

                if added_lines_in_method or deleted_lines_in_method:
                    if self.ignore_comments:
                        # We ignore only comments changed in the method
                        if set([str(token) for token in before.tokens]) == set(
                            [str(token) for token in after.tokens]
                        ):
                            added_lines -= added_lines_in_method
                            deleted_lines -= deleted_lines_in_method
                            continue
                    if added_lines_in_method:
                        before.added_lines = after.added_lines
                        added_lines -= added_lines_in_method
                    if deleted_lines_in_method:
                        after.deleted_lines = before.deleted_lines
                        deleted_lines -= deleted_lines_in_method
                    method_changes_commit.methods_before.add(before)
                    method_changes_commit.methods_after.add(after)

        if method_changes_commit.methods_before:
            return method_changes_commit

        return None

    @staticmethod
    def _syntax_error(code: str) -> bool:
        try:
            parse(code)
            return False
        except JavaSyntaxError:
            return True
        except Exception as e:
            # print(e)
            # print(code)
            return True

    @staticmethod
    def save(commit: MethodChangesCommit, base_dir: str) -> None:
        # save this object to a file
        try:
            path = Path(base_dir) / commit.repo / f"{commit.commit_hash}.pkl"
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                pickle.dump(commit, f)
        except Exception as e:
            print(e)
            raise e

    @staticmethod
    def load(
        base_dir: str, repo: str, commit_hash: str
    ) -> Optional[MethodChangesCommit]:
        try:
            path = Path(base_dir) / repo / f"{commit_hash}.pkl"
            with open(path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError as e:
            print("Not found cache file")
            return None

    @staticmethod
    def check(base_dir: str, repo: str, commit_hash: str) -> bool:
        path = Path(base_dir) / repo / f"{commit_hash}.pkl"
        return path.exists()
    

def commit_from(
    project: str, commit_hash: str, base_dir: str = "data/repo"
) -> Union[Commit, Exception]:
    repo_path = f"{base_dir}/{project}"
    if not Path(repo_path).exists():
        Repo.clone_from(f"https://github.com/apache/{project}.git", repo_path)
    try:
        return Git(repo_path).get_commit(commit_hash)

    except Exception as e:
        git_lock = Path(repo_path) / ".git" / "config.lock"
        if git_lock.exists():
            git_lock.unlink()
            return commit_from(project, commit_hash, base_dir)
        else:
            return type(e)


def issue_key_from(project: str, commit_hash: str) -> str:
    commit = commit_from(project, commit_hash)

    # Jira issue key pattern
    pattern = re.compile(r"([A-Z]+-\d+)")
    match = pattern.search(commit.msg)
    if match:
        return match.group(1)
    else:
        return None
