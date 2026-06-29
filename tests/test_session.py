import importlib.util
import unittest
import uuid
from pathlib import Path

_SESSION_PATH = Path(__file__).resolve().parents[1] / "plugin" / "session.py"
_spec = importlib.util.spec_from_file_location("ferrosa_session_under_test", _SESSION_PATH)
session = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(session)


class FerrosaSessionIdTests(unittest.TestCase):
    def setUp(self):
        self.ns = session.DEFAULT_SESSION_NS

    def test_deterministic(self):
        a = session.ferrosa_session_id("20260628_134834_d90c1c66", self.ns)
        b = session.ferrosa_session_id("20260628_134834_d90c1c66", self.ns)
        self.assertEqual(a, b)

    def test_distinct_inputs_distinct_uuids(self):
        a = session.ferrosa_session_id("session-a", self.ns)
        b = session.ferrosa_session_id("session-b", self.ns)
        self.assertNotEqual(a, b)

    def test_output_is_valid_uuid(self):
        out = session.ferrosa_session_id("anything", self.ns)
        self.assertEqual(str(uuid.UUID(out)), out)

    def test_valid_uuid_passthrough(self):
        existing = "b4c62491-fb35-4fbb-b670-5f29dd2d5adf"
        self.assertEqual(session.ferrosa_session_id(existing, self.ns), existing)

    def test_empty_and_none_return_none(self):
        self.assertIsNone(session.ferrosa_session_id("", self.ns))
        self.assertIsNone(session.ferrosa_session_id("   ", self.ns))
        self.assertIsNone(session.ferrosa_session_id(None, self.ns))


class ResolveSessionNamespaceTests(unittest.TestCase):
    def test_blank_returns_default(self):
        self.assertEqual(session.resolve_session_namespace({}), session.DEFAULT_SESSION_NS)
        self.assertEqual(
            session.resolve_session_namespace({"FERROSA_MEMORY_SESSION_NS": "  "}),
            session.DEFAULT_SESSION_NS,
        )

    def test_uuid_env_used_directly(self):
        ns = "11111111-1111-1111-1111-111111111111"
        self.assertEqual(
            session.resolve_session_namespace({"FERROSA_MEMORY_SESSION_NS": ns}),
            uuid.UUID(ns),
        )

    def test_arbitrary_string_env_derives_stable_namespace(self):
        env = {"FERROSA_MEMORY_SESSION_NS": "team-alpha"}
        ns1 = session.resolve_session_namespace(env)
        ns2 = session.resolve_session_namespace(env)
        self.assertEqual(ns1, ns2)
        self.assertNotEqual(ns1, session.DEFAULT_SESSION_NS)

    def test_namespace_override_changes_mapping(self):
        default_out = session.ferrosa_session_id("s1", session.DEFAULT_SESSION_NS)
        other_ns = session.resolve_session_namespace({"FERROSA_MEMORY_SESSION_NS": "team-alpha"})
        self.assertNotEqual(session.ferrosa_session_id("s1", other_ns), default_out)


if __name__ == "__main__":
    unittest.main()
