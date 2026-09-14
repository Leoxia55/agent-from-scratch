"""skills.py 单元测试：技能发现与管理。"""

from __future__ import annotations

from pathlib import Path

from scratchagent.skills import (
    SkillInfo,
    discover_skills,
    generate_skills_prompt,
    load_skill,
    parse_frontmatter,
)


# ---------------------------------------------------------------- parse_frontmatter
class TestParseFrontmatter:
    def test_valid(self):
        content = "---\nname: csv-analysis\ndescription: Analyze CSV\n---\n\nbody"
        fm = parse_frontmatter(content)
        assert fm == {"name": "csv-analysis", "description": "Analyze CSV"}

    def test_missing(self):
        assert parse_frontmatter("no frontmatter here") == {}

    def test_strips_quotes(self):
        content = '---\nname: "csv"\ndescription: \'desc\'\n---'
        fm = parse_frontmatter(content)
        assert fm["name"] == "csv"
        assert fm["description"] == "desc"


# ---------------------------------------------------------------- load_skill
class TestLoadSkill:
    def test_missing_skill_md(self, tmp_path):
        d = tmp_path / "skill"
        d.mkdir()
        assert load_skill(d) is None

    def test_missing_name_or_desc(self, tmp_path):
        d = tmp_path / "skill"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: x\n---\nbody", encoding="utf-8")
        assert load_skill(d) is None

    def test_returns_skill_info(self, tmp_path):
        d = tmp_path / "skill"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: csv-analysis\ndescription: Analyze CSV\n---\n# body",
            encoding="utf-8",
        )
        info = load_skill(d)
        assert info is not None
        assert info.name == "csv-analysis"
        assert info.description == "Analyze CSV"
        assert isinstance(info.path, Path)


# ---------------------------------------------------------------- discover_skills
class TestDiscoverSkills:
    def test_discovers_all(self, tmp_path):
        for name in ("a", "b", "c"):
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: desc {name}\n---\nbody",
                encoding="utf-8",
            )
        skills = discover_skills(tmp_path)
        assert len(skills) == 3
        assert {s.name for s in skills} == {"a", "b", "c"}

    def test_skips_hidden(self, tmp_path):
        (tmp_path / ".git").mkdir()
        d = tmp_path / "real"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: real\ndescription: desc\n---\nbody", encoding="utf-8"
        )
        skills = discover_skills(tmp_path)
        assert len(skills) == 1
        assert skills[0].name == "real"

    def test_nonexistent_path(self, tmp_path):
        assert discover_skills(tmp_path / "missing") == []

    def test_skips_invalid_skill(self, tmp_path):
        (tmp_path / "invalid").mkdir()  # 无 SKILL.md
        d = tmp_path / "valid"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: valid\ndescription: desc\n---\nbody", encoding="utf-8"
        )
        skills = discover_skills(tmp_path)
        assert len(skills) == 1
        assert skills[0].name == "valid"


# ---------------------------------------------------------------- generate_skills_prompt
class TestGenerateSkillsPrompt:
    def test_empty(self):
        assert generate_skills_prompt([]) == ""

    def test_lists_all(self):
        skills = [
            SkillInfo(name="a", description="desc a", path=Path("/x/a")),
            SkillInfo(name="b", description="desc b", path=Path("/x/b")),
        ]
        prompt = generate_skills_prompt(skills)
        assert "### a" in prompt
        assert "### b" in prompt
        assert "desc a" in prompt
        assert "/home/user/skills/a/" in prompt
