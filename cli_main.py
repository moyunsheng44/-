from engine.game import Game


def main() -> None:
    game = Game.create_default_game()
    print("命令行调试模式已启动。")
    print("这个入口仅用于调试；正式游玩请运行 main.py。")
    print("当前窗口版已经取代了旧的命令行交互。")
    state = game.start_game()
    print(f"当前回合：{state['turn_number']}，行动方：{state['current_player']['name']}")
    for line in state["logs"]:
        print(line)


if __name__ == "__main__":
    main()
