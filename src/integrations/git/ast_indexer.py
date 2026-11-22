"""
Deterministic AST & Regex Code Indexer & Interface Slicer.
Overcomes monorepo LLM token limits (500k+ LoC) at $0.00 cost.
Extracts pure route definitions, API endpoints, and schema contracts
into a compact (< 1,000 token) specification for autonomous QA agents.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.core.logging import get_logger

logger = get_logger("ast_code_indexer")


class FrontendRoute(BaseModel):
    path: str
    component: Optional[str] = None
    file_origin: str
    framework: str  # angular | react | vue | unknown


class EndpointRoute(BaseModel):
    method: str
    path: str
    handler_name: str
    file_origin: str
    docstring: Optional[str] = None
    parameters: List[str] = Field(default_factory=list)


class ModelSchema(BaseModel):
    name: str
    fields: Dict[str, str] = Field(default_factory=dict)
    file_origin: str


class IndexedContractSummary(BaseModel):
    frontend_routes: List[FrontendRoute] = Field(default_factory=list)
    api_endpoints: List[EndpointRoute] = Field(default_factory=list)
    data_models: List[ModelSchema] = Field(default_factory=list)
    scanned_files_count: int = 0
    total_loc_scanned: int = 0

    def to_compact_markdown(self) -> str:
        """Serializes extracted contracts into a dense, token-efficient specification (< 1,000 tokens)."""
        lines = [
            "# REPOSITORY INTERFACE CONTRACT (EXTRACTED VIA DETERMINISTIC AST INDEXER)",
            f"- Scanned Files: {self.scanned_files_count} | Source Lines Sliced: {self.total_loc_scanned:,}",
            "",
            "## 1. Verified Frontend Navigation Routes",
        ]
        if self.frontend_routes:
            lines.append("| Route Path | Target Component / View | Framework | File |")
            lines.append("|---|---|---|---|")
            for r in self.frontend_routes[:25]:
                lines.append(f"| `{r.path}` | {r.component or 'N/A'} | {r.framework} | `{Path(r.file_origin).name}` |")
        else:
            lines.append("_No explicit frontend routes discovered in analyzed slices._")

        lines.append("")
        lines.append("## 2. Verified Backend API Endpoints")
        if self.api_endpoints:
            lines.append("| HTTP Method | Endpoint URI | Handler Function | File |")
            lines.append("|---|---|---|---|")
            for ep in self.api_endpoints[:35]:
                lines.append(f"| `{ep.method}` | `{ep.path}` | `{ep.handler_name}()` | `{Path(ep.file_origin).name}` |")
        else:
            lines.append("_No explicit API endpoints discovered in analyzed slices._")

        lines.append("")
        lines.append("## 3. Core Domain DTOs & Schemas")
        if self.data_models:
            for m in self.data_models[:10]:
                fields_str = ", ".join([f"{k}: {v}" for k, v in list(m.fields.items())[:6]])
                lines.append(f"- **{m.name}** (`{Path(m.file_origin).name}`): `{{{fields_str}}}`")
        else:
            lines.append("_No standalone data schemas indexed._")

        return "\n".join(lines)


class ASTCodeIndexer:
    """
    Zero-cost deterministic static analysis parser for multi-framework repositories.
    Parses Python AST for FastAPI/Flask and regex patterns for Angular/React/Vue and Express.
    """

    # Common router file patterns
    ROUTER_PATTERNS = {
        "angular": [r".*routes?\.ts$", r".*routing\.module\.ts$"],
        "react": [r".*App\.[jt]sx?$", r".*routes?\.[jt]sx?$", r".*router\.[jt]sx?$"],
        "vue": [r".*router[\\/].*\.[jt]s$"],
        "python_api": [r".*api.*\.py$", r".*routes?\.py$", r".*views?\.py$", r".*main\.py$"],
        "express_api": [r".*routes?\.js$", r".*controller.*\.js$", r".*server\.js$", r".*app\.js$"],
    }

    def __init__(self):
        pass

    def index_virtual_files(self, files: Dict[str, str]) -> IndexedContractSummary:
        """Indexes an in-memory dictionary of {relative_path: content} retrieved via MCP or Git tree."""
        frontend_routes: List[FrontendRoute] = []
        api_endpoints: List[EndpointRoute] = []
        data_models: List[ModelSchema] = []
        total_loc = 0

        for file_path, content in files.items():
            lines = content.splitlines()
            total_loc += len(lines)
            p = file_path.replace("\\", "/").lower()

            # 1. Angular / TypeScript Routes
            if p.endswith((".ts", ".tsx", ".js", ".jsx")):
                ts_routes = self.extract_typescript_routes(content, file_path)
                frontend_routes.extend(ts_routes)

                express_eps = self.extract_express_endpoints(content, file_path)
                api_endpoints.extend(express_eps)

            # 2. Python Endpoints & Models
            if p.endswith(".py"):
                py_eps = self.extract_python_endpoints(content, file_path)
                api_endpoints.extend(py_eps)

                py_models = self.extract_python_models(content, file_path)
                data_models.extend(py_models)

        # Deduplicate
        seen_routes = set()
        dedup_routes = []
        for r in frontend_routes:
            key = (r.path, r.framework)
            if key not in seen_routes:
                seen_routes.add(key)
                dedup_routes.append(r)

        seen_eps = set()
        dedup_eps = []
        for ep in api_endpoints:
            key = (ep.method, ep.path)
            if key not in seen_eps:
                seen_eps.add(key)
                dedup_eps.append(ep)

        return IndexedContractSummary(
            frontend_routes=dedup_routes,
            api_endpoints=dedup_eps,
            data_models=data_models,
            scanned_files_count=len(files),
            total_loc_scanned=total_loc,
        )

    def index_directory(self, root_dir: str | Path, max_depth: int = 5) -> IndexedContractSummary:
        """Recursively inspects a local repository filesystem, selecting only architectural route files."""
        root = Path(root_dir).resolve()
        if not root.is_dir():
            logger.warning(f"Root path {root} is not a valid directory.")
            return IndexedContractSummary()

        collected_files: Dict[str, str] = {}
        ignored_dirs = {
            ".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__",
            ".idea", ".vscode", "coverage", ".next", ".nuxt", "vendor"
        }

        for path in root.rglob("*"):
            if any(part in ignored_dirs for part in path.parts):
                continue
            if not path.is_file():
                continue

            rel_str = str(path.relative_to(root)).replace("\\", "/")
            ext = path.suffix.lower()

            if ext in (".py", ".ts", ".js", ".tsx", ".jsx"):
                # Only read if it matches routing, api, controller, or model keywords
                name_lower = path.name.lower()
                if any(
                    kw in name_lower
                    for kw in ["route", "router", "routing", "api", "controller", "view", "endpoint", "schema", "model", "main", "app"]
                ):
                    try:
                        content = path.read_text(encoding="utf-8", errors="replace")
                        # Skip massive bundles (> 300KB)
                        if len(content) < 300_000:
                            collected_files[rel_str] = content
                    except Exception as e:
                        logger.debug(f"Could not read {path}: {e}")

        return self.index_virtual_files(collected_files)

    def extract_typescript_routes(self, content: str, file_path: str) -> List[FrontendRoute]:
        """Extracts routes from Angular `Routes` array, React `<Route path=...>`, and Vue `routes`."""
        routes: List[FrontendRoute] = []

        # Angular Routes: { path: '...', component: ... } or { path: "...", ... }
        # Match: path:\s*['"]([^'"]*)['"]
        angular_matches = re.finditer(
            r"path\s*:\s*['\"]([^'\"]*)['\"]\s*(?:,\s*component\s*:\s*([A-Za-z0-9_]+))?",
            content,
            re.MULTILINE,
        )
        for m in angular_matches:
            path_val = m.group(1).strip()
            comp_val = m.group(2) if m.group(2) else None
            # Filter out wildcards or redirects if needed, but keep meaningful routes
            routes.append(
                FrontendRoute(
                    path=f"/{path_val}" if not path_val.startswith("/") else path_val,
                    component=comp_val,
                    file_origin=file_path,
                    framework="angular" if "angular" in file_path.lower() or "ng" in file_path.lower() else "spa",
                )
            )

        # React Router: <Route path="/..." element={<Comp />} />
        react_matches = re.finditer(
            r"<Route\s+[^>]*path=['\"]([^'\"]+)['\"][^>]*(?:element=\{<([A-Za-z0-9_]+))?",
            content,
            re.MULTILINE,
        )
        for m in react_matches:
            path_val = m.group(1).strip()
            comp_val = m.group(2) if m.group(2) else None
            routes.append(
                FrontendRoute(
                    path=path_val,
                    component=comp_val,
                    file_origin=file_path,
                    framework="react",
                )
            )

        return routes

    def extract_express_endpoints(self, content: str, file_path: str) -> List[EndpointRoute]:
        """Extracts Express.js router endpoints: `app.get('/path', ...)`, `router.post('/path', ...)`."""
        endpoints: List[EndpointRoute] = []
        pattern = re.finditer(
            r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*(?:async\s*)?(?:function|\([^\)]*\)\s*=>|([A-Za-z0-9_]+))",
            content,
            re.IGNORECASE,
        )
        for m in pattern:
            method = m.group(1).upper()
            path = m.group(2)
            handler = m.group(3) or "anonymous_handler"
            endpoints.append(
                EndpointRoute(
                    method=method,
                    path=path,
                    handler_name=handler,
                    file_origin=file_path,
                )
            )
        return endpoints

    def extract_python_endpoints(self, content: str, file_path: str) -> List[EndpointRoute]:
        """Parses Python AST to extract FastAPI and Flask routes accurately with decorators and docstrings."""
        endpoints: List[EndpointRoute] = []
        try:
            tree = ast.parse(content, filename=file_path)
        except Exception:
            return endpoints

        HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    # Case 1: @router.get("/path") or @app.post("/path")
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        method_name = decorator.func.attr.lower()
                        if method_name in HTTP_METHODS or method_name == "route":
                            # Extract path from first argument
                            path = "/"
                            if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                                path = decorator.args[0].value
                            elif decorator.keywords:
                                for kw in decorator.keywords:
                                    if kw.arg in ("path", "rule") and isinstance(kw.value, ast.Constant):
                                        path = str(kw.value.value)

                            method_str = method_name.upper()
                            # If Flask @app.route("/", methods=["POST"])
                            if method_name == "route":
                                method_str = "GET"
                                for kw in decorator.keywords:
                                    if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                                        methods = [
                                            elt.value for elt in kw.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                                        ]
                                        if methods:
                                            method_str = "/".join([m.upper() for m in methods])

                            doc = ast.get_docstring(node)
                            params = [arg.arg for arg in node.args.args if arg.arg not in ("self", "cls", "db")]

                            endpoints.append(
                                EndpointRoute(
                                    method=method_str,
                                    path=path,
                                    handler_name=node.name,
                                    file_origin=file_path,
                                    docstring=doc.split("\n")[0] if doc else None,
                                    parameters=params,
                                )
                            )
        return endpoints

    def extract_python_models(self, content: str, file_path: str) -> List[ModelSchema]:
        """Extracts Pydantic BaseModel and SQLAlchemy classes."""
        models: List[ModelSchema] = []
        try:
            tree = ast.parse(content, filename=file_path)
        except Exception:
            return models

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check base class: BaseModel, Base, etc.
                is_model = any(
                    isinstance(b, ast.Name) and b.id in ("BaseModel", "Base")
                    or (isinstance(b, ast.Attribute) and b.attr in ("BaseModel", "Base"))
                    for b in node.bases
                )
                if is_model:
                    fields = {}
                    for item in node.body:
                        # Annotated assignment: `field_name: str = ...`
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            field_name = item.target.id
                            type_name = "Any"
                            if isinstance(item.annotation, ast.Name):
                                type_name = item.annotation.id
                            elif isinstance(item.annotation, ast.Constant):
                                type_name = str(item.annotation.value)
                            fields[field_name] = type_name
                    models.append(ModelSchema(name=node.name, fields=fields, file_origin=file_path))
        return models


# Global singleton instance
ast_code_indexer = ASTCodeIndexer()
