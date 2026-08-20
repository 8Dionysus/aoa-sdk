KNOWN_REPOS = (
    "8Dionysus",
    "aoa-sdk",
    "aoa-routing",
    "aoa-skills",
    "aoa-agents",
    "aoa-playbooks",
    "aoa-memo",
    "aoa-evals",
    "aoa-kag",
    "aoa-stats",
    "aoa-dashboard",
    "aoa-techniques",
    "Agents-of-Abyss",
    "Tree-of-Sophia",
    "Dionysus",
    "abyss-stack",
)

WORKSPACE_REQUIRED_REPOS = (
    "8Dionysus",
    "Agents-of-Abyss",
    "Tree-of-Sophia",
    "Dionysus",
    "aoa-agents",
    "aoa-evals",
    "aoa-kag",
    "aoa-memo",
    "aoa-playbooks",
    "aoa-sdk",
    "aoa-skills",
    "aoa-stats",
    "aoa-techniques",
)

WORKSPACE_OPTIONAL_REPOS = (
    "aoa-routing",
    "aoa-dashboard",
    "abyss-stack",
)

# Discovery membership is deliberately not mutation authority. Keep these
# owner sets explicit so a newly discovered optional organ cannot become a
# release or checkpoint target by being added to KNOWN_REPOS.
OWNER_MUTABLE_REPOS = (
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

OWNER_RELEASE_REPOS = (
    "aoa-sdk",
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
    "aoa-sdk",
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
