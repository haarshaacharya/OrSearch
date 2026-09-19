from .planner import create_plan
from .computer import execute_action
from .vision import analyze_screen


def run_agent(user_request):
    try:
        if not user_request or not user_request.strip():
            return {
                "success": False,
                "message": "Empty request.",
                "actions": [],
                "plan": None
            }

        plan = create_plan(user_request)

        actions = plan.get("actions", [])

        results = []

        for action in actions:
            action_type = action.get("type", "")

            if action_type == "analyze_screen":
                instruction = action.get(
                    "parameter",
                    "Describe the current screen and identify useful UI elements."
                )

                result = analyze_screen(instruction)

            else:
                result = execute_action(action)

            results.append(
                {
                    "action": action,
                    "result": result
                }
            )

        return {
            "success": True,
            "message": "Task completed.",
            "actions": results,
            "plan": plan
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Agent error: {e}",
            "actions": [],
            "plan": None
        }


if __name__ == "__main__":
    print("Orsearch Backend Agent")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in {"exit", "quit"}:
                break

            result = run_agent(user_input)

            print("\nOrsearch:")
            print(result)

        except KeyboardInterrupt:
            print("\nExiting...")
            break

        except Exception as e:
            print(f"\nError: {e}")