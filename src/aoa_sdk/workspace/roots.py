KNOWN_REPOS = (
    "aoa-sdk",
    "aoa-routing",
    "aoa-skills",
    "aoa-agents",
    "aoa-playbooks",
    "aoa-memo",
    "aoa-evals",
    "aoa-kag",
    "aoa-stats",
    "aoa-techniques",
    "Agents-of-Abyss",
    "Tree-of-Sophia",
    "Dionysus",
    "abyss-stack",
)

CORE_FEDERATION_REPOS = (
    "aoa-routing",
    "aoa-skills",
    "aoa-agents",
)

REPO_MARKERS = (
    ".git",
    "README.md",
    "AGENTS.md",
    "pyproject.toml",
    "generated",
)

DEFAULT_EXTERNAL_ROOT_PATTERNS = (
    "~/src",
)

DEFAULT_PREFERRED_REPO_PATH_PATTERNS = {
    "abyss-stack": (
        "~/src/abyss-stack",
    ),
}
