from openai_agent.smart_suggestion_generator import _format_conversation


def test_format_conversation() -> None:
    messages = [
        {
            "role": "assistant",
            "content": """Welcome aboard! I'm Captn, your digital marketing companion.
            Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing.
            Before we set sail, could you steer our course by sharing the business goal you'd like to improve?""",
        },
        {"role": "user", "content": "I want to Boost sales"},
        {
            "role": "assistant",
            "content": "Awesome goal! Let's set sail and boost your sales.",
        },
        {"role": "user", "content": "Am excited to get started!"},
    ]
    expected = """chatbot: Welcome aboard! I'm Captn, your digital marketing companion.
            Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing.
            Before we set sail, could you steer our course by sharing the business goal you'd like to improve?
customer: I want to Boost sales
chatbot: Awesome goal! Let's set sail and boost your sales.
customer: Am excited to get started!"""
    actual = _format_conversation(messages)
    print(actual)
    print(expected)
    assert actual == expected
