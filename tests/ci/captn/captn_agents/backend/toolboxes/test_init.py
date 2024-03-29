def test_init() -> None:
    from captn.captn_agents.backend.toolboxes import __all__

    assert len(__all__) >= 2
