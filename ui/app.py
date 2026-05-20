from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from engine.game import Game
from utils.display import effect_label, target_label


CARD_WIDTH = 140
CARD_HEIGHT = 160
CARD_GAP = 10
ZONE_WIDTH = 920
ZONE_MIN_HEIGHT = 220
HAND_MIN_HEIGHT = 250


class CardGameApp:
    def __init__(self) -> None:
        self.game = Game.create_default_game()
        self.root = tk.Tk()
        self.root.title("钢铁战线")
        self.root.geometry("1540x980")
        self.root.minsize(1400, 1000)
        self.root.configure(bg="#0b1219")

        self.selected_hand_index: int | None = None
        self.selected_friendly_unit_index: int | None = None
        self.selected_enemy_unit_index: int | None = None
        self._end_dialog_shown = False
        self._hover_cache: dict[int, str] = {}
        self._card_frames: dict[str, tk.Frame] = {}

        self.status_var = tk.StringVar()
        self.selection_var = tk.StringVar(value="当前未选择任何目标。")
        self.detail_var = tk.StringVar(value="请先选择一张手牌或一个单位。")
        self.target_hint_var = tk.StringVar(value="目标提示：当前没有需要补充的目标。")
        self.mana_flash_var = tk.StringVar(value="")
        self.mana_change_var = tk.StringVar(value="当前没有费用变化")
        self.settings_music_var = tk.StringVar(value="开启")
        self.settings_speed_var = tk.StringVar(value="标准")
        self.collection_search_var = tk.StringVar()
        self.collection_type_var = tk.StringVar(value="全部")
        self.collection_sort_var = tk.StringVar(value="默认")

        self.action_buttons: dict[str, ttk.Button] = {}
        self.friendly_hq_health_fill: tk.Frame | None = None
        self.enemy_hq_health_fill: tk.Frame | None = None
        self.collection_entries: list[dict] = []

        self._configure_style()
        self._build_pages()
        self.show_page("home")

    def run(self) -> None:
        self.root.mainloop()

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Root.TFrame", background="#0b1219")
        style.configure("BattleStage.TFrame", background="#0f1822")
        style.configure("SidePanel.TFrame", background="#101923")
        style.configure("Panel.TLabelframe", background="#101923", foreground="#cfc7b5", borderwidth=0, relief="flat")
        style.configure("Panel.TLabelframe.Label", background="#101923", foreground="#cfc7b5")
        style.configure("CardZone.TLabelframe", background="#0f1822", foreground="#f3e8d6", borderwidth=0, relief="flat")
        style.configure("CardZone.TLabelframe.Label", background="#0f1822", foreground="#f3e8d6")
        style.configure("Frontline.TLabelframe", background="#142430", foreground="#f4dfb5", borderwidth=0, relief="flat")
        style.configure("Frontline.TLabelframe.Label", background="#142430", foreground="#f4dfb5")
        style.configure("Title.TLabel", background="#0b1219", foreground="#f8eedb")
        style.configure("SubTitle.TLabel", background="#0b1219", foreground="#c9d3de")
        style.configure("Info.TLabel", background="#101923", foreground="#c7c0b0")
        style.configure("Hint.TLabel", background="#182636", foreground="#ffd89c")
        style.configure("Action.TButton", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("CompactAction.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=(6, 4))
        style.map(
            "Action.TButton",
            background=[("disabled", "#394550"), ("active", "#c1943f"), ("!disabled", "#8d6b2d")],
            foreground=[("disabled", "#9ea7b1"), ("!disabled", "#fff4df")],
        )
        style.map(
            "CompactAction.TButton",
            background=[("disabled", "#394550"), ("active", "#c1943f"), ("!disabled", "#8d6b2d")],
            foreground=[("disabled", "#9ea7b1"), ("!disabled", "#fff4df")],
        )

    def _build_pages(self) -> None:
        self.pages: dict[str, tk.Frame] = {}
        self.page_container = tk.Frame(self.root, bg="#0b1219")
        self.page_container.pack(fill="both", expand=True)

        self.home_page = tk.Frame(self.page_container, bg="#0b1219")
        self.collection_page = tk.Frame(self.page_container, bg="#0b1219")
        self.settings_page = tk.Frame(self.page_container, bg="#0b1219")
        self.battle_page = tk.Frame(self.page_container, bg="#0b1219")

        self.pages["home"] = self.home_page
        self.pages["collection"] = self.collection_page
        self.pages["settings"] = self.settings_page
        self.pages["battle"] = self.battle_page

        for frame in self.pages.values():
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_home_page()
        self._build_collection_page()
        self._build_settings_page()
        self._build_battle_page()

    def show_page(self, name: str) -> None:
        self.pages[name].lift()

    def _build_home_page(self) -> None:
        frame = self.home_page
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        hero = tk.Frame(frame, bg="#15110d", highlightbackground="#8c6a3d", highlightthickness=2)
        hero.place(relx=0.5, rely=0.5, anchor="center", width=920, height=640)

        banner = tk.Canvas(hero, bg="#15110d", highlightthickness=0)
        banner.place(x=0, y=0, relwidth=1, height=220)
        banner.create_rectangle(0, 0, 920, 220, fill="#30261d", outline="")
        banner.create_text(460, 70, text="钢铁战线", fill="#f3e6cf", font=("Microsoft YaHei UI", 38, "bold"))
        banner.create_text(
            460,
            122,
            text="在硝烟、泥泞与装甲洪流中争夺前线，直至敌方总部沦陷。",
            fill="#d7c7ab",
            font=("Microsoft YaHei UI", 13),
        )
        banner.create_line(170, 162, 750, 162, fill="#8c6a3d", width=2)
        banner.create_text(460, 190, text="FRONTLINE • ARMOR • COMMAND", fill="#9f8b73", font=("Consolas", 12))

        menu = tk.Frame(hero, bg="#15110d")
        menu.place(relx=0.5, rely=0.67, anchor="center")
        home_buttons = [
            ("开始战斗", self._start_battle_from_home),
            ("收藏", lambda: self.show_page("collection")),
            ("结束游戏", self._confirm_exit),
            ("设置", lambda: self.show_page("settings")),
        ]
        for row, (label, command) in enumerate(home_buttons):
            ttk.Button(menu, text=label, command=command, style="Action.TButton").grid(
                row=row, column=0, pady=10, ipadx=54, ipady=10
            )

        footer = tk.Label(
            hero,
            text="双人轮流制卡牌原型 | 前线推进 | 总部打击 | 指令协同",
            bg="#15110d",
            fg="#9f9485",
            font=("Microsoft YaHei UI", 10),
        )
        footer.place(relx=0.5, rely=0.93, anchor="center")

    def _build_collection_page(self) -> None:
        frame = self.collection_page
        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(2, weight=1)

        header = tk.Frame(frame, bg="#0b1219")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 12))
        header.columnconfigure(0, weight=1)
        tk.Label(
            header,
            text="收藏与卡牌管理",
            bg="#0b1219",
            fg="#f7edd8",
            font=("Microsoft YaHei UI", 24, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="返回开始页面", command=lambda: self.show_page("home"), style="Action.TButton").grid(
            row=0, column=1, sticky="e"
        )

        filter_bar = tk.Frame(frame, bg="#0b1219")
        filter_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 12))
        tk.Label(filter_bar, text="搜索", bg="#0b1219", fg="#f1e4cc", font=("Microsoft YaHei UI", 10, "bold")).grid(row=0, column=0, padx=(0, 8))
        search_entry = ttk.Entry(filter_bar, textvariable=self.collection_search_var, width=24)
        search_entry.grid(row=0, column=1, padx=(0, 14))
        search_entry.bind("<KeyRelease>", self._refresh_collection_filters)
        tk.Label(filter_bar, text="类型", bg="#0b1219", fg="#f1e4cc", font=("Microsoft YaHei UI", 10, "bold")).grid(row=0, column=2, padx=(0, 8))
        type_box = ttk.Combobox(filter_bar, textvariable=self.collection_type_var, values=["全部", "单位", "步兵", "坦克", "指令"], width=10)
        type_box.grid(row=0, column=3, padx=(0, 14))
        type_box.bind("<<ComboboxSelected>>", self._refresh_collection_filters)
        tk.Label(filter_bar, text="排序", bg="#0b1219", fg="#f1e4cc", font=("Microsoft YaHei UI", 10, "bold")).grid(row=0, column=4, padx=(0, 8))
        sort_box = ttk.Combobox(filter_bar, textvariable=self.collection_sort_var, values=["默认", "费用升序", "费用降序", "类型"], width=12)
        sort_box.grid(row=0, column=5)
        sort_box.bind("<<ComboboxSelected>>", self._refresh_collection_filters)

        self.collection_list = tk.Listbox(
            frame,
            font=("Microsoft YaHei UI", 11),
            bg="#132130",
            fg="#f2e7d1",
            selectbackground="#c1943f",
            selectforeground="#17100a",
            activestyle="none",
        )
        self.collection_list.grid(row=2, column=0, sticky="nsew", padx=(24, 12), pady=(0, 24))
        self.collection_list.bind("<<ListboxSelect>>", self._on_collection_select)

        self.collection_detail = tk.Text(
            frame,
            bg="#111c29",
            fg="#ecdfc9",
            font=("Microsoft YaHei UI", 11),
            wrap="word",
            relief="flat",
        )
        self.collection_detail.grid(row=2, column=1, sticky="nsew", padx=(12, 24), pady=(0, 24))
        self.collection_detail.insert("1.0", "这里会显示卡牌的详细介绍、类型、效果、战术建议与加入收藏说明。")
        self.collection_detail.config(state="disabled")
        self._populate_collection_list()

    def _build_settings_page(self) -> None:
        frame = self.settings_page
        frame.columnconfigure(0, weight=1)
        header = tk.Frame(frame, bg="#0b1219")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 16))
        header.columnconfigure(0, weight=1)
        tk.Label(
            header,
            text="设置",
            bg="#0b1219",
            fg="#f7edd8",
            font=("Microsoft YaHei UI", 24, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="返回开始页面", command=lambda: self.show_page("home"), style="Action.TButton").grid(
            row=0, column=1, sticky="e"
        )

        settings_card = tk.Frame(frame, bg="#162231", padx=24, pady=24, width=520, height=280)
        settings_card.grid(row=1, column=0, sticky="nw", padx=24, pady=(0, 24))
        settings_card.grid_propagate(False)

        tk.Label(settings_card, text="音乐提示", bg="#162231", fg="#efe2cc", font=("Microsoft YaHei UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Combobox(settings_card, textvariable=self.settings_music_var, values=["开启", "关闭"], width=12).grid(
            row=0, column=1, sticky="w", pady=(0, 8), padx=(16, 0)
        )
        tk.Label(settings_card, text="动画速度", bg="#162231", fg="#efe2cc", font=("Microsoft YaHei UI", 12, "bold")).grid(row=1, column=0, sticky="w", pady=(0, 8))
        ttk.Combobox(settings_card, textvariable=self.settings_speed_var, values=["标准", "较快", "较慢"], width=12).grid(
            row=1, column=1, sticky="w", pady=(0, 8), padx=(16, 0)
        )
        tk.Label(
            settings_card,
            text="提示：动画速度会影响总部受击和费用变动的表现节奏。",
            bg="#162231",
            fg="#bfc8d2",
            font=("Microsoft YaHei UI", 10),
            wraplength=420,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def _build_battle_page(self) -> None:
        page = self.battle_page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(page, style="Root.TFrame", padding=16)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=8)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(1, weight=1)

        header = ttk.Frame(main_frame, style="Root.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)

        title_block = ttk.Frame(header, style="Root.TFrame")
        title_block.grid(row=0, column=0, sticky="w")
        ttk.Label(title_block, text="钢铁战线：战斗界面", style="Title.TLabel", font=("Microsoft YaHei UI", 24, "bold")).grid(row=0, column=0, sticky="w")
        self.turn_subtitle = ttk.Label(title_block, text="", style="SubTitle.TLabel", font=("Microsoft YaHei UI", 10))
        self.turn_subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))

        header_buttons = tk.Frame(header, bg="#0b1219")
        header_buttons.grid(row=0, column=1, sticky="e")
        ttk.Button(header_buttons, text="返回开始页面", command=lambda: self.show_page("home"), style="Action.TButton").grid(row=0, column=0, padx=(0, 8))
        ttk.Button(header_buttons, text="重新开始一局", command=self._restart_game, style="Action.TButton").grid(row=0, column=1)

        battle_body = ttk.Frame(main_frame, style="Root.TFrame")
        battle_body.grid(row=1, column=0, columnspan=2, sticky="nsew")
        battle_body.columnconfigure(0, weight=8)
        battle_body.columnconfigure(1, weight=3)
        battle_body.rowconfigure(0, weight=1)

        board_shell = ttk.Frame(battle_body, style="BattleStage.TFrame", padding=12)
        board_shell.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        board_shell.columnconfigure(0, weight=1)
        board_shell.rowconfigure(0, weight=1)
        board_column = ttk.Frame(board_shell, style="BattleStage.TFrame")
        board_column.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        board_column.columnconfigure(0, weight=1)
        board_column.rowconfigure(0, weight=0, minsize=ZONE_MIN_HEIGHT)
        board_column.rowconfigure(1, weight=0, minsize=ZONE_MIN_HEIGHT)
        board_column.rowconfigure(2, weight=0, minsize=ZONE_MIN_HEIGHT)
        board_column.rowconfigure(3, weight=1, minsize=HAND_MIN_HEIGHT)

        self.enemy_frame = self._create_zone_frame(board_column, "敌方后方战场", 0)
        self.enemy_cards_container = self._create_zone_container(self.enemy_frame, frontline=False)

        self.frontline_frame = self._create_zone_frame(board_column, "前线战场", 1)
        self.frontline_cards_container = self._create_zone_container(self.frontline_frame, frontline=True)

        self.friendly_frame = self._create_zone_frame(board_column, "我方后方战场", 2)
        self.friendly_cards_container = self._create_zone_container(self.friendly_frame, frontline=False)

        self.friendly_frame.grid_configure(pady=(0, 0))

        self.hand_frame = ttk.LabelFrame(board_column, text="手牌区  滚轮上下滑动", style="CardZone.TLabelframe", padding=8)
        self.hand_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 0))
        self.hand_frame.columnconfigure(0, weight=0)
        self.hand_frame.columnconfigure(1, weight=1)
        self.hand_frame.rowconfigure(0, weight=1)
        self.hand_label = tk.Label(self.hand_frame, text="手\n牌", bg="#101b27", fg="#98a7b7",
                                    font=("Microsoft YaHei UI", 10, "bold"), justify="center")
        self.hand_label.grid(row=0, column=0, sticky="ns", padx=(4, 6))
        self.hand_canvas = tk.Canvas(self.hand_frame, bg="#111b25", highlightthickness=0,
                                      yscrollincrement=CARD_HEIGHT + CARD_GAP)
        self.hand_canvas.grid(row=0, column=1, sticky="nsew")
        self.hand_cards_container = tk.Frame(self.hand_canvas, bg="#111b25")
        self.hand_canvas_window = self.hand_canvas.create_window((0, 0), window=self.hand_cards_container, anchor="nw")
        self.hand_cards_container.bind("<Configure>", self._on_hand_container_configure)
        self.hand_canvas.bind("<Configure>", self._on_hand_canvas_configure)
        self._bind_hand_wheel()

        side_column = ttk.Frame(battle_body, style="SidePanel.TFrame", padding=4)
        side_column.grid(row=0, column=1, sticky="nsew")
        side_column.columnconfigure(0, weight=1)
        side_column.rowconfigure(0, weight=0)
        side_column.rowconfigure(1, weight=0)
        side_column.rowconfigure(2, weight=1)

        self.status_panel = ttk.LabelFrame(side_column, text="战场概览", style="Panel.TLabelframe", padding=8)
        self.status_panel.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.status_panel.columnconfigure(0, weight=1)
        ttk.Label(
            self.status_panel,
            textvariable=self.status_var,
            style="Info.TLabel",
            justify="left",
            font=("Microsoft YaHei UI", 11),
            wraplength=360,
        ).grid(row=0, column=0, sticky="ew")
        tk.Label(
            self.status_panel,
            textvariable=self.mana_flash_var,
            bg="#101923",
            fg="#ffdf87",
            font=("Microsoft YaHei UI", 10, "bold"),
            anchor="w",
            wraplength=360,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self.command_frame = ttk.LabelFrame(side_column, text="战术面板", style="Panel.TLabelframe", padding=8)
        self.command_frame.grid(row=1, column=0, sticky="ew")
        self.command_frame.columnconfigure(0, weight=1)

        self.command_frame.columnconfigure(0, weight=1)
        self.command_frame.columnconfigure(1, weight=1)

        ttk.Label(self.command_frame, textvariable=self.selection_var, style="Hint.TLabel", wraplength=360, justify="left", font=("Microsoft YaHei UI", 10), padding=6).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.mana_change_panel = tk.Label(
            self.command_frame,
            textvariable=self.mana_change_var,
            bg="#2a2214",
            fg="#ffe39e",
            font=("Microsoft YaHei UI", 10, "bold"),
            wraplength=360,
            justify="left",
            anchor="w",
            padx=10,
            pady=6,
        )
        self.mana_change_panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Label(self.command_frame, textvariable=self.target_hint_var, style="Info.TLabel", wraplength=360, justify="left", font=("Microsoft YaHei UI", 10)).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Label(self.command_frame, textvariable=self.detail_var, style="Info.TLabel", wraplength=360, justify="left", font=("Microsoft YaHei UI", 10)).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        buttons = [
            ("play_card", "打出选中手牌", self._play_selected_card),
            ("move_front", "推进到前线", self._move_frontline),
            ("attack_unit", "攻击敌方单位", self._attack_enemy_unit),
            ("attack_hq", "攻击敌方总部", self._attack_enemy_hq),
            ("end_turn", "结束回合", self._end_turn),
            ("clear", "清除选择", self._clear_selection),
            ("help", "查看说明", self._show_help),
        ]
        for offset, (key, label, command) in enumerate(buttons):
            row = 4 + offset // 2
            column = offset % 2
            button = ttk.Button(self.command_frame, text=label, command=command, style="CompactAction.TButton")
            button.grid(row=row, column=column, sticky="ew", pady=2, padx=3, ipady=1)
            self.action_buttons[key] = button

        log_frame = ttk.LabelFrame(side_column, text="战斗日志", style="Panel.TLabelframe", padding=6)
        log_frame.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            state="disabled",
            font=("Microsoft YaHei UI", 10),
            bg="#101821",
            fg="#ddd2c0",
            relief="flat",
            insertbackground="#f2e6d2",
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

    def _create_zone_frame(self, parent: tk.Frame, title: str, row: int) -> ttk.LabelFrame:
        style = "Frontline.TLabelframe" if "前线" in title else "CardZone.TLabelframe"
        pady = (0, 8)
        frame = ttk.LabelFrame(parent, text=title, style=style, padding=8)
        frame.grid(row=row, column=0, sticky="nsew", pady=pady)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        return frame

    def _create_zone_container(self, frame: ttk.LabelFrame, frontline: bool) -> tk.Frame:
        container = tk.Frame(
            frame,
            bg="#152733" if frontline else "#111b25",
        )
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_propagate(False)
        return container

    def _start_battle_from_home(self) -> None:
        self.game = Game.create_default_game()
        self.selected_hand_index = None
        self.selected_friendly_unit_index = None
        self.selected_enemy_unit_index = None
        self._end_dialog_shown = False
        self.game.start_game()
        self.show_page("battle")
        self.refresh_view()

    def refresh_view(self) -> None:
        self._card_frames.clear()
        state = self.game.get_state()
        self.status_var.set(state["status_text"])
        turn = state["turn_number"]
        player = state["current_player"]["name"]
        self.turn_subtitle.configure(text=f"第 {turn} 回合 · {player} 行动阶段")
        self._render_battle_zone(self.enemy_cards_container, state["opponent"], friendly=False)
        self._render_frontline_zone(state)
        self._render_battle_zone(self.friendly_cards_container, state["current_player"], friendly=True)
        self._render_hand_cards(state["current_player"]["hand"])
        self._set_logs(state["logs"])
        self._update_selection_text()
        self._update_detail_panel()
        self._update_zone_titles(state)
        self._update_button_states(state)
        self._flash_mana_info(state)
        if state["game_over"] and not self._end_dialog_shown:
            winner = state["winner"] or "无人"
            self._end_dialog_shown = True
            messagebox.showinfo("游戏结束", f"本局结束，胜利者：{winner}")

    def _render_battle_zone(self, container: tk.Frame, owner: dict, friendly: bool) -> None:
        self._clear_card_container(container)
        hq_frame = self._create_hq_card(container, owner, friendly)
        zone_height = container.winfo_height()
        if zone_height < 100:
            zone_height = ZONE_MIN_HEIGHT - 16
        card_y = self._safe_card_y(zone_height, top_padding=6, bottom_padding=16)
        hq_frame.place(x=12, y=card_y)
        backline_units = owner["backline"]
        if not backline_units:
            self._render_empty_text(container, "暂无后方单位。", x=184)
            return
        for offset, card in enumerate(backline_units):
            selected = card["index"] == self.selected_friendly_unit_index if friendly else card["index"] == self.selected_enemy_unit_index
            accent = "#66c28c" if friendly else "#d9775d"
            frame = self._create_unit_card(container, card, accent, selected, friendly)
            frame.place(x=self._backline_slot_x(offset), y=card_y)

    def _render_frontline_zone(self, state: dict) -> None:
        self._clear_card_container(self.frontline_cards_container)
        friendly_front = state["current_player"]["frontline"]
        enemy_front = state["opponent"]["frontline"]

        if not friendly_front and not enemy_front:
            self._render_empty_text(self.frontline_cards_container, "当前没有单位驻扎在前线。", x=290)
            return

        zone_height = self.frontline_cards_container.winfo_height()
        if zone_height < 100:
            zone_height = ZONE_MIN_HEIGHT - 16
        card_y = self._safe_card_y(zone_height, top_padding=6, bottom_padding=16)
        for offset, card in enumerate(enemy_front):
            selected = card["index"] == self.selected_enemy_unit_index
            frame = self._create_unit_card(self.frontline_cards_container, card, "#c66a50", selected, False)
            frame.place(x=self._frontline_enemy_slot_x(offset), y=card_y)

        for offset, card in enumerate(friendly_front):
            selected = card["index"] == self.selected_friendly_unit_index
            frame = self._create_unit_card(self.frontline_cards_container, card, "#59b77a", selected, True)
            frame.place(x=self._frontline_friendly_slot_x(offset), y=card_y)

    def _create_unit_card(self, parent: tk.Frame, card: dict, accent: str, selected: bool, friendly: bool) -> tk.Frame:
        key = f"{'friendly' if friendly else 'enemy'}_{card['index']}"
        effects = card.get("effects", [])
        keywords = [e["description"] for e in effects if e["trigger"] in ("on_deploy", "on_move", "on_attack", "on_death")]
        effects_desc = [e["description"] for e in effects if e["trigger"] == "aura"]
        keywords_text = " | ".join(keywords) if keywords else ""
        effects_text = " | ".join(effects_desc) if effects_desc else ""
        return self._create_card_block(
            parent=parent,
            title=card["name"],
            subtitle=f"{card['unit_class']} | {'前线' if card['in_frontline'] else '后方'}",
            body="",
            accent=accent,
            icon=card["emblem"],
            selected=selected,
            command=(lambda idx=card["index"]: self._select_friendly_unit(idx)) if friendly else (lambda idx=card["index"]: self._select_enemy_unit(idx)),
            detail_lines=[
                f"名称：{card['name']}",
                f"类型：{card['unit_class']}",
                f"攻击：{card['attack']}    生命：{card['health']}",
                f"部署费用：{card['cost']}    行动花费：{card['action_cost']}",
                f"位置：{'前线' if card['in_frontline'] else '后方'}",
                f"介绍：{card['description']}",
            ],
            key=key,
            card_kind="unit",
            attack_value=card["attack"],
            health_value=card["health"],
            deploy_cost=card["cost"],
            action_cost=card.get("action_cost", 0),
            keywords_text=keywords_text,
            effects_text=effects_text,
            draggable=friendly,
        )

    def _create_hq_card(self, parent: tk.Frame, owner: dict, friendly: bool) -> tk.Frame:
        accent = "#3d7b61" if friendly else "#9c4037"
        key = "hq_friendly" if friendly else "hq_enemy"
        frame = self._create_card_block(
            parent=parent,
            title=f"{owner['name']} 总部",
            subtitle=f"生命 {owner['health']} / 20",
            body="总部据点",
            accent=accent,
            icon="⌂",
            selected=False,
            command=lambda: None,
            detail_lines=[
                f"总部：{owner['name']}",
                f"当前生命：{owner['health']} / 20",
                "规则：只有敌方前线单位才能直接攻击总部。",
            ],
            key=key,
            card_kind="hq",
            health_value=owner["health"],
        )
        bar_outer = tk.Frame(frame, bg="#2d3946", height=16)
        bar_outer.place(x=6, y=CARD_HEIGHT - 30, width=CARD_WIDTH - 12)
        fill_width = max(10, int((CARD_WIDTH - 12) * owner["health"] / 20))
        fill = tk.Frame(bar_outer, bg="#d95f4f" if not friendly else "#4fb879", width=fill_width)
        fill.place(x=0, y=0, relheight=1)
        tk.Label(bar_outer, text=f"{owner['health']} / 20", bg="#2d3946", fg="#fff4e6", font=("Microsoft YaHei UI", 8, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        if friendly:
            self.friendly_hq_health_fill = fill
        else:
            self.enemy_hq_health_fill = fill
        return frame

    def _backline_slot_x(self, slot_index: int) -> int:
        return 12 + (CARD_WIDTH + CARD_GAP) * (slot_index + 1)

    def _frontline_enemy_slot_x(self, slot_index: int) -> int:
        return 156 + slot_index * (CARD_WIDTH + CARD_GAP)

    def _frontline_friendly_slot_x(self, slot_index: int) -> int:
        return 156 + slot_index * (CARD_WIDTH + CARD_GAP)

    def _safe_card_y(self, container_height: int, top_padding: int = 8, bottom_padding: int = 22) -> int:
        usable_height = max(CARD_HEIGHT, container_height - top_padding - bottom_padding)
        centered_y = top_padding + max(0, (usable_height - CARD_HEIGHT) // 2)
        max_y = max(top_padding, container_height - CARD_HEIGHT - bottom_padding)
        return min(centered_y, max_y)

    def _render_hand_cards(self, cards: list[dict]) -> None:
        self._clear_card_container(self.hand_cards_container)
        cols = 5
        canvas_h = self.hand_canvas.winfo_height()
        if canvas_h < 100:
            canvas_h = 160
        if not cards:
            self._render_empty_text(self.hand_cards_container, "当前没有手牌。", x=16)
            self.hand_cards_container.configure(width=578, height=canvas_h)
            self.hand_canvas.configure(scrollregion=(0, 0, 578, canvas_h))
            return

        for index, card in enumerate(cards):
            row = index // cols
            col = index % cols
            cx = 6 + col * (CARD_WIDTH + CARD_GAP)
            cy = 6 + row * (CARD_HEIGHT + CARD_GAP)
            is_unit = card["card_type"] == "unit"
            body = "" if is_unit else f"部署 {card['cost']} / {effect_label(card['effect_type'])} {card['effect_value']}"
            details = [
                f"名称：{card['name']}",
                f"部署费用：{card['cost']}",
                f"介绍：{card['description']}",
            ]
            if is_unit:
                details.insert(1, f"类型：{card['unit_class']}")
                details.append(f"行动花费：{card['action_cost']}")
                details.append(f"攻击：{card['attack']}    生命：{card['health']}")
            else:
                details.insert(1, "类型：指令")
                details.append(f"效果：{effect_label(card['effect_type'])} {card['effect_value']}，目标 {target_label(card['target_type'])}")

            effects = card.get("effects", [])
            keywords = [e["description"] for e in effects if e["trigger"] != "aura"]
            auras = [e["description"] for e in effects if e["trigger"] == "aura"]
            keywords_text = " | ".join(keywords) if keywords else ""
            effects_text = " | ".join(auras) if auras else ""
            frame = self._create_card_block(
                parent=self.hand_cards_container,
                title=card["name"],
                subtitle=card["unit_class"] if is_unit else "指令",
                body=body,
                accent="#d2a25a" if is_unit else "#5fb0d6",
                icon=card["emblem"],
                selected=index == self.selected_hand_index,
                command=lambda idx=index: self._select_hand_card(idx),
                detail_lines=details,
                key=f"hand_{index}",
                card_kind=card["card_type"],
                attack_value=card["attack"] if is_unit else None,
                health_value=card["health"] if is_unit else None,
                deploy_cost=card["cost"] if is_unit else None,
                action_cost=card.get("action_cost", 0) if is_unit else None,
                keywords_text=keywords_text,
                effects_text=effects_text,
                draggable=True,
            )
            frame.place(x=cx, y=cy)

        rows = (len(cards) + cols - 1) // cols
        container_w = 6 + cols * CARD_WIDTH + (cols - 1) * CARD_GAP
        container_h = max(canvas_h, 6 + rows * (CARD_HEIGHT + CARD_GAP) - CARD_GAP)
        self.hand_cards_container.configure(width=container_w, height=container_h)
        self.hand_canvas.configure(scrollregion=(0, 0, container_w, container_h))

    def _create_card_block(
        self,
        parent: tk.Frame,
        title: str,
        subtitle: str,
        body: str,
        accent: str,
        icon: str,
        selected: bool,
        command,
        detail_lines: list[str],
        key: str | None = None,
        card_kind: str = "unit",
        attack_value: int | None = None,
        health_value: int | None = None,
        deploy_cost: int | None = None,
        action_cost: int | None = None,
        keywords_text: str = "",
        effects_text: str = "",
        draggable: bool = False,
    ) -> tk.Frame:
        border = "#f4cd75" if selected else accent
        frame = tk.Frame(
            parent,
            bg="#1a2430",
            highlightbackground=border,
            highlightcolor=border,
            highlightthickness=3 if selected else 1,
            bd=0,
            cursor="hand2",
            width=CARD_WIDTH,
            height=CARD_HEIGHT,
        )
        frame._accent = accent
        frame._card_key = key
        frame._card_kind = card_kind
        frame._draggable = draggable
        frame._command = command
        if key is not None:
            self._card_frames[key] = frame
        self._bind_card_events(frame, command, border, detail_lines)

        title_label = tk.Label(frame, text=title, bg=accent, fg="#081018", font=("Microsoft YaHei UI", 10, "bold"), wraplength=CARD_WIDTH - 16, justify="center", anchor="center")
        title_label.place(x=6, y=6, width=CARD_WIDTH - 12, height=28)
        self._bind_card_events(title_label, command, border, detail_lines, parent_frame=frame)

        subtitle_label = tk.Label(frame, text=subtitle, bg="#1a2430", fg="#d5dce5", font=("Microsoft YaHei UI", 8), wraplength=CARD_WIDTH - 16, justify="left", anchor="w")
        subtitle_label.place(x=8, y=38, width=CARD_WIDTH - 16, height=20)
        self._bind_card_events(subtitle_label, command, border, detail_lines, parent_frame=frame)

        if keywords_text:
            kw_label = tk.Label(frame, text=keywords_text, bg="#1a2430", fg="#e2c266", font=("Microsoft YaHei UI", 7, "bold"), wraplength=CARD_WIDTH - 16, justify="left", anchor="w")
            kw_label.place(x=8, y=62, width=CARD_WIDTH - 16, height=20)
            self._bind_card_events(kw_label, command, border, detail_lines, parent_frame=frame)

        if effects_text:
            eff_label = tk.Label(frame, text=effects_text, bg="#1a2430", fg="#c9a85b", font=("Microsoft YaHei UI", 7), wraplength=CARD_WIDTH - 16, justify="left", anchor="nw")
            eff_label.place(x=8, y=86, width=CARD_WIDTH - 16, height=16)
            self._bind_card_events(eff_label, command, border, detail_lines, parent_frame=frame)
        elif body:
            body_label = tk.Label(frame, text=body, bg="#1a2430", fg="#b8c2cf", font=("Microsoft YaHei UI", 8), wraplength=CARD_WIDTH - 16, justify="left", anchor="nw")
            body_label.place(x=8, y=86, width=CARD_WIDTH - 16, height=20)
            self._bind_card_events(body_label, command, border, detail_lines, parent_frame=frame)

        if card_kind == "unit":
            badge_w = 36
            cost_y = CARD_HEIGHT - 42
            if deploy_cost is not None:
                dep_badge = tk.Label(frame, text=str(deploy_cost), bg="#8d6b2d", fg="#fff8e4", font=("Microsoft YaHei UI", 9, "bold"))
                dep_badge.place(x=8, y=cost_y, width=badge_w, height=18)
                self._bind_card_events(dep_badge, command, border, detail_lines, parent_frame=frame)
            if action_cost is not None:
                act_badge = tk.Label(frame, text=str(action_cost), bg="#2d5f8a", fg="#e8f1fc", font=("Microsoft YaHei UI", 9, "bold"))
                act_badge.place(x=CARD_WIDTH - 8 - badge_w, y=cost_y, width=badge_w, height=18)
                self._bind_card_events(act_badge, command, border, detail_lines, parent_frame=frame)
            if deploy_cost is not None or action_cost is not None:
                cost_label = tk.Label(frame, text="部 / 行", bg="#1a2430", fg="#98a7b7", font=("Microsoft YaHei UI", 7))
                cost_label.place(x=8 + badge_w + 4, y=cost_y + 2, width=CARD_WIDTH - 16 - badge_w * 2 - 8, height=14)
                self._bind_card_events(cost_label, command, border, detail_lines, parent_frame=frame)

            atk_y = CARD_HEIGHT - 22
            atk_badge = tk.Label(frame, text=str(attack_value or 0), bg="#8e4336", fg="#fff0e8", font=("Microsoft YaHei UI", 9, "bold"))
            atk_badge.place(x=8, y=atk_y, width=badge_w, height=18)
            hp_badge = tk.Label(frame, text=str(health_value or 0), bg="#2d6b4a", fg="#eefcf3", font=("Microsoft YaHei UI", 9, "bold"))
            hp_badge.place(x=CARD_WIDTH - 8 - badge_w, y=atk_y, width=badge_w, height=18)
            atk_label = tk.Label(frame, text="攻 / 生", bg="#1a2430", fg="#98a7b7", font=("Microsoft YaHei UI", 7))
            atk_label.place(x=8 + badge_w + 4, y=atk_y + 2, width=CARD_WIDTH - 16 - badge_w * 2 - 8, height=14)
            self._bind_card_events(atk_badge, command, border, detail_lines, parent_frame=frame)
            self._bind_card_events(hp_badge, command, border, detail_lines, parent_frame=frame)
            self._bind_card_events(atk_label, command, border, detail_lines, parent_frame=frame)
        return frame

    def _bind_card_events(self, widget: tk.Widget, command, border: str, detail_lines: list[str], parent_frame: tk.Frame | None = None) -> None:
        target = parent_frame or widget
        widget.bind("<Button-1>", lambda _event: self._handle_card_click(command))
        widget.bind("<Double-Button-1>", lambda _event: self._handle_card_double_click(detail_lines))
        widget.bind("<Enter>", lambda _event: self._animate_hover(target, border, True))
        widget.bind("<Leave>", lambda _event: self._animate_hover(target, border, False))

    def _show_card_detail(self, detail_lines: list[str]) -> None:
        messagebox.showinfo("卡牌详情", "\n".join(detail_lines))

    def _handle_card_click(self, command) -> str:
        command()
        return "break"

    def _handle_card_double_click(self, detail_lines: list[str]) -> str:
        self._show_card_detail(detail_lines)
        return "break"

    def _animate_hover(self, frame: tk.Frame, border: str, entering: bool) -> None:
        frame_id = id(frame)
        if frame_id not in self._hover_cache:
            self._hover_cache[frame_id] = border
        base_border = self._hover_cache[frame_id]
        if entering:
            frame.configure(highlightbackground="#fff2ab", highlightcolor="#fff2ab", bg="#1f2b38")
            frame.lift()
        else:
            frame.configure(bg="#1a2430", highlightbackground=base_border, highlightcolor=base_border)

    def _set_logs(self, logs: list[str]) -> None:
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, "\n".join(logs))
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _clear_card_container(self, container: tk.Frame) -> None:
        for child in container.winfo_children():
            self._hover_cache.pop(id(child), None)
            child.destroy()

    def _render_empty_text(self, container: tk.Frame, message: str, x: int) -> None:
        center_y = max(48, container.winfo_height() // 2 - 20)
        tk.Label(container, text=message, bg=container.cget("bg"), fg="#92a0af", font=("Microsoft YaHei UI", 11), pady=16).place(x=x, y=center_y)

    def _select_hand_card(self, index: int) -> None:
        if self.selected_hand_index is not None:
            self._set_card_selected(f"hand_{self.selected_hand_index}", False)
        self.selected_hand_index = index if self.selected_hand_index != index else None
        if self.selected_hand_index is not None:
            self._set_card_selected(f"hand_{self.selected_hand_index}", True)
        self._update_selection_text()
        self._update_detail_panel()
        self._update_button_states(self.game.get_state())

    def _select_friendly_unit(self, index: int) -> None:
        if self.selected_friendly_unit_index is not None:
            self._set_card_selected(f"friendly_{self.selected_friendly_unit_index}", False)
        self.selected_friendly_unit_index = index if self.selected_friendly_unit_index != index else None
        if self.selected_friendly_unit_index is not None:
            self._set_card_selected(f"friendly_{self.selected_friendly_unit_index}", True)
        self._update_selection_text()
        self._update_detail_panel()
        self._update_button_states(self.game.get_state())

    def _select_enemy_unit(self, index: int) -> None:
        if self.selected_enemy_unit_index is not None:
            self._set_card_selected(f"enemy_{self.selected_enemy_unit_index}", False)
        self.selected_enemy_unit_index = index if self.selected_enemy_unit_index != index else None
        if self.selected_enemy_unit_index is not None:
            self._set_card_selected(f"enemy_{self.selected_enemy_unit_index}", True)
        self._update_selection_text()
        self._update_detail_panel()
        self._update_button_states(self.game.get_state())

    def _set_card_selected(self, key: str, selected: bool) -> None:
        frame = self._card_frames.get(key)
        if frame is None:
            return
        accent = getattr(frame, '_accent', '#1f2630')
        if selected:
            frame.configure(highlightthickness=3, highlightbackground="#f4cd75", highlightcolor="#f4cd75")
        else:
            frame.configure(highlightthickness=1, highlightbackground=accent, highlightcolor=accent)

    def _play_selected_card(self) -> None:
        if self.selected_hand_index is None:
            self._show_error("请先选择一张手牌。")
            return
        target = self._infer_card_target()
        selected_name = self._selected_hand_name()
        self._run_action(lambda: self.game.play_card(self.selected_hand_index, target), "play", selected_name)
        self._clear_selection()

    def _move_frontline(self) -> None:
        if self.selected_friendly_unit_index is None:
            self._show_error("请先选择一个我方单位。")
            return
        self._run_action(lambda: self.game.move_to_frontline(self.selected_friendly_unit_index), "move_front", self._selected_friendly_name())

    def _attack_enemy_unit(self) -> None:
        if self.selected_friendly_unit_index is None:
            self._show_error("请先选择一个我方单位。")
            return
        if self.selected_enemy_unit_index is None:
            self._show_error("请再选择一个敌方单位作为攻击目标。")
            return
        self._run_action(
            lambda: self.game.attack(self.selected_friendly_unit_index, "enemy_unit", self.selected_enemy_unit_index),
            "attack_unit",
            self._selected_friendly_name(),
        )
        self._clear_selection()

    def _attack_enemy_hq(self) -> None:
        if self.selected_hand_index is not None:
            self._run_action(lambda: self.game.play_card(self.selected_hand_index, ("enemy_player", None)), "attack_hq", self._selected_hand_name())
        elif self.selected_friendly_unit_index is not None:
            self._run_action(lambda: self.game.attack(self.selected_friendly_unit_index, "enemy_player", None), "attack_hq", self._selected_friendly_name())
        else:
            self._show_error("请先选择一张指令牌或一个我方单位。")
            return
        self._clear_selection()

    def _end_turn(self) -> None:
        self._run_action(self.game.end_turn, "turn", "结束回合")
        self._clear_selection()

    def _restart_game(self) -> None:
        if not messagebox.askyesno("重新开始", "确定要重新开始这一局吗？"):
            return
        self._end_dialog_shown = False
        self.game.reset_game()
        self._clear_selection()
        self.refresh_view()

    def _show_help(self) -> None:
        messagebox.showinfo("操作说明", self.game.get_state()["help_text"])

    def _confirm_exit(self) -> None:
        if messagebox.askyesno("结束游戏", "确定要结束游戏并关闭窗口吗？"):
            self.root.destroy()
        else:
            self.show_page("home")

    def _clear_selection(self) -> None:
        if self.selected_hand_index is not None:
            self._set_card_selected(f"hand_{self.selected_hand_index}", False)
        if self.selected_friendly_unit_index is not None:
            self._set_card_selected(f"friendly_{self.selected_friendly_unit_index}", False)
        if self.selected_enemy_unit_index is not None:
            self._set_card_selected(f"enemy_{self.selected_enemy_unit_index}", False)
        self.selected_hand_index = None
        self.selected_friendly_unit_index = None
        self.selected_enemy_unit_index = None
        self._update_selection_text()
        self._update_detail_panel()
        self._update_button_states(self.game.get_state())

    def _update_selection_text(self) -> None:
        parts: list[str] = []
        if self.selected_hand_index is not None:
            parts.append(f"已选手牌：{self._selected_hand_name()}")
        if self.selected_friendly_unit_index is not None:
            parts.append(f"已选我方单位：{self._selected_friendly_name()}")
        if self.selected_enemy_unit_index is not None:
            parts.append(f"已选敌方单位：{self._selected_enemy_name()}")
        self.selection_var.set("；".join(parts) if parts else "当前未选择任何目标。")
        self.target_hint_var.set(self._build_target_hint())

    def _update_detail_panel(self) -> None:
        state = self.game.get_state()
        detail_lines: list[str] = []
        if self.selected_hand_index is not None:
            hand = state["current_player"]["hand"]
            if self.selected_hand_index < len(hand):
                card = hand[self.selected_hand_index]
                detail_lines.append(f"手牌：{card['name']}")
                if card["card_type"] == "unit":
                    detail_lines.append(f"{card['unit_class']} | 部署 {card['cost']} | 行动花费 {card['action_cost']}")
                else:
                    detail_lines.append(f"指令 | 部署 {card['cost']} | {effect_label(card['effect_type'])} {card['effect_value']}")
                detail_lines.append("双击卡牌可查看完整详情。")
        elif self.selected_friendly_unit_index is not None:
            board = state["current_player"]["board"]
            unit = next((item for item in board if item["index"] == self.selected_friendly_unit_index), None)
            if unit:
                detail_lines.append(f"我方单位：{unit['name']}")
                detail_lines.append(f"{unit['unit_class']} | 攻 {unit['attack']} 生 {unit['health']} | 行动花费 {unit['action_cost']}")
                detail_lines.append("双击单位可查看完整详情。")
        elif self.selected_enemy_unit_index is not None:
            board = state["opponent"]["board"]
            unit = next((item for item in board if item["index"] == self.selected_enemy_unit_index), None)
            if unit:
                detail_lines.append(f"敌方单位：{unit['name']}")
                detail_lines.append(f"{unit['unit_class']} | 攻 {unit['attack']} 生 {unit['health']} | 行动花费 {unit['action_cost']}")
                detail_lines.append("双击单位可查看完整详情。")
        else:
            detail_lines.append("请先选择一张手牌或一个单位。")
            detail_lines.append("推荐流程：部署单位 -> 推进前线 -> 攻击单位或总部。")
            detail_lines.append("费用变化会在右侧战术面板独立显示。")
        self.detail_var.set("\n".join(detail_lines))

    def _update_zone_titles(self, state: dict) -> None:
        current_name = state["current_player"]["name"]
        frontline_owner = state["frontline_owner"] or "无"
        frontline_count = len(state["opponent"]["frontline"]) + len(state["current_player"]["frontline"])
        max_back = state["max_backline_units"]
        max_front = state["max_frontline_units"]
        self.enemy_frame.configure(text=f"敌方后方战场  单位 {len(state['opponent']['backline'])}/{max_back}")
        self.friendly_frame.configure(text=f"我方后方战场  单位 {len(state['current_player']['backline'])}/{max_back}")
        self.frontline_frame.configure(text=f"◆ 前线战场  占领方：{frontline_owner}  单位 {frontline_count}/{max_front}")
        self.hand_frame.configure(text=f"手牌  {state['current_player']['hand_count']}/10  滚轮上下滑动")
        self.command_frame.configure(text=f"战术面板  {current_name}")

    def _update_button_states(self, state: dict) -> None:
        game_over = state["game_over"]
        hand_selected = self.selected_hand_index is not None
        friendly_selected = self.selected_friendly_unit_index is not None
        enemy_selected = self.selected_enemy_unit_index is not None
        current_unit = None
        if friendly_selected:
            current_unit = next((item for item in state["current_player"]["board"] if item["index"] == self.selected_friendly_unit_index), None)

        can_attack = bool(current_unit)
        if can_attack and current_unit["unit_class"] in ("步兵", "坦克") and not current_unit["in_frontline"]:
            can_attack = False

        self._set_button_state("play_card", hand_selected and not game_over)
        self._set_button_state("move_front", bool(current_unit and not current_unit["in_frontline"]) and not game_over)
        self._set_button_state("attack_unit", can_attack and enemy_selected and not game_over)
        self._set_button_state("attack_hq", (hand_selected or can_attack) and not game_over)
        self._set_button_state("end_turn", not game_over)
        self._set_button_state("clear", (hand_selected or friendly_selected or enemy_selected) and not game_over)
        self._set_button_state("help", True)

    def _set_button_state(self, key: str, enabled: bool) -> None:
        self.action_buttons[key].state(["!disabled"] if enabled else ["disabled"])

    def _flash_mana_info(self, state: dict) -> None:
        current = state["current_player"]
        mana_change = state["last_mana_change"]
        change_text = (
            f"{mana_change.get('label', '无')}：{mana_change.get('before', current['mana'])} -> {mana_change.get('after', current['mana'])}"
            if mana_change
            else "当前没有费用变化"
        )
        self.mana_flash_var.set(
            f"当前剩余费用：{current['mana']} / {current['max_mana']}    后方单位：{len(current['backline'])}/4    前线单位：{len(current['frontline'])}/5"
        )
        self.mana_change_var.set(change_text)

    def _build_target_hint(self) -> str:
        if self.selected_hand_index is not None:
            hand = self.game.get_state()["current_player"]["hand"]
            if self.selected_hand_index < len(hand):
                target_type = hand[self.selected_hand_index]["target_type"]
                if target_type is None:
                    return "目标提示：这张牌不需要额外目标，直接点击“打出选中手牌”即可。"
                if target_type == "enemy_unit":
                    return "目标提示：这是一张指向敌方单位的指令，请再选择一个敌方单位。"
                if target_type == "enemy_player":
                    return "目标提示：这张指令会作用于敌方总部，可直接点击“攻击敌方总部”。"
                if target_type == "ally_unit":
                    return "目标提示：这是一张支援我方单位的指令，请再选择一个我方单位。"
                if target_type == "ally_player":
                    return "目标提示：这张指令会作用于我方总部，直接点击“打出选中手牌”即可。"
        if self.selected_friendly_unit_index is not None:
            return "目标提示：你已选择我方单位，可以推进到前线，或在满足条件时发动攻击。"
        if self.selected_enemy_unit_index is not None:
            return "目标提示：你已选择敌方单位，如果要发起攻击，请再选择一个我方单位。"
        return "目标提示：当前没有需要补充的目标。"

    def _infer_card_target(self) -> tuple[str, int | None] | None:
        if self.selected_hand_index is None:
            return None
        current_hand = self.game.get_state()["current_player"]["hand"]
        selected = current_hand[self.selected_hand_index]
        target_type = selected["target_type"]
        if target_type == "enemy_unit":
            if self.selected_enemy_unit_index is None:
                raise ValueError("这张指令需要先选择一个敌方单位。")
            return ("enemy_unit", self.selected_enemy_unit_index)
        if target_type == "enemy_player":
            return ("enemy_player", None)
        if target_type == "ally_unit":
            if self.selected_friendly_unit_index is None:
                raise ValueError("这张指令需要先选择一个我方单位。")
            return ("ally_unit", self.selected_friendly_unit_index)
        if target_type == "ally_player":
            return ("ally_player", None)
        return None

    def _run_action(self, action, action_kind: str, focus_name: str) -> None:
        try:
            action()
        except ValueError as error:
            self._show_error(str(error))
            return
        self.refresh_view()
        if action_kind == "attack_hq":
            self._animate_hq_health(self.enemy_hq_health_fill, self.game.get_state()["opponent"]["health"])

    def _animate_hq_health(self, fill: tk.Frame | None, health: int) -> None:
        if fill is None:
            return
        target_width = max(10, int((CARD_WIDTH - 12) * health / 20))
        current_width = fill.winfo_width() or target_width
        step = -4 if current_width > target_width else 4

        def tick() -> None:
            nonlocal current_width
            if (step < 0 and current_width <= target_width) or (step > 0 and current_width >= target_width):
                fill.configure(width=target_width)
                return
            current_width += step
            fill.configure(width=current_width)
            self.root.after(25, tick)

        tick()

    def _populate_collection_list(self) -> None:
        self.collection_entries = list(self.game.get_state()["card_library"])
        self._refresh_collection_filters()

    def _refresh_collection_filters(self, _event: object | None = None) -> None:
        query = self.collection_search_var.get().strip().lower()
        type_filter = self.collection_type_var.get()
        sort_mode = self.collection_sort_var.get()
        entries = list(self.game.get_state()["card_library"])

        if query:
            entries = [entry for entry in entries if query in entry["name"].lower() or query in entry["description"].lower()]
        if type_filter != "全部":
            if type_filter == "指令":
                entries = [entry for entry in entries if entry["card_type"] == "spell"]
            elif type_filter == "单位":
                entries = [entry for entry in entries if entry["card_type"] == "unit"]
            else:
                entries = [entry for entry in entries if entry.get("unit_class") == type_filter]
        if sort_mode == "费用升序":
            entries.sort(key=lambda item: item["cost"])
        elif sort_mode == "费用降序":
            entries.sort(key=lambda item: item["cost"], reverse=True)
        elif sort_mode == "类型":
            entries.sort(key=lambda item: (item["card_type"], item["cost"], item["name"]))

        self.collection_entries = entries
        self.collection_list.delete(0, tk.END)
        for entry in entries:
            if entry["card_type"] == "unit":
                label = f"{entry['name']} | {entry['unit_class']} | 部署 {entry['cost']} | 行动 {entry['action_cost']} | {entry['attack']}/{entry['health']}"
            else:
                label = f"{entry['name']} | 指令 | 费用 {entry['cost']} | {effect_label(entry['effect_type'])} {entry['effect_value']}"
            self.collection_list.insert(tk.END, label)

    def _on_collection_select(self, _event: object) -> None:
        selection = self.collection_list.curselection()
        if not selection:
            return
        entry = self.collection_entries[selection[0]]
        lines = [
            f"名称：{entry['name']}",
            f"类型：{'单位 - ' + entry['unit_class'] if entry['card_type'] == 'unit' else '指令'}",
            f"部署费用：{entry['cost']}",
            f"说明：{entry['description']}",
        ]
        if entry["card_type"] == "unit":
            lines.append(f"行动花费：{entry['action_cost']}")
            lines.append(f"数值：攻击 {entry['attack']} / 生命 {entry['health']}")
        else:
            lines.append(f"效果：{effect_label(entry['effect_type'])} {entry['effect_value']}，目标 {target_label(entry['target_type'])}")
        self.collection_detail.config(state="normal")
        self.collection_detail.delete("1.0", tk.END)
        self.collection_detail.insert("1.0", "\n".join(lines))
        self.collection_detail.config(state="disabled")

    def _selected_hand_name(self) -> str:
        hand = self.game.get_state()["current_player"]["hand"]
        if self.selected_hand_index is None or self.selected_hand_index >= len(hand):
            return "未知手牌"
        return hand[self.selected_hand_index]["name"]

    def _selected_friendly_name(self) -> str:
        unit = next((item for item in self.game.get_state()["current_player"]["board"] if item["index"] == self.selected_friendly_unit_index), None)
        return unit["name"] if unit else "未知单位"

    def _selected_enemy_name(self) -> str:
        unit = next((item for item in self.game.get_state()["opponent"]["board"] if item["index"] == self.selected_enemy_unit_index), None)
        return unit["name"] if unit else "未知单位"

    def _on_hand_container_configure(self, _event: object) -> None:
        self.hand_canvas.configure(scrollregion=self.hand_canvas.bbox("all"))

    def _on_hand_canvas_configure(self, event: tk.Event) -> None:
        self.hand_canvas.itemconfigure(
            self.hand_canvas_window,
            width=max(event.width, self.hand_cards_container.winfo_reqwidth()),
        )

    def _bind_hand_wheel(self) -> None:
        for widget in (self.hand_canvas, self.hand_cards_container, self.hand_frame):
            widget.bind("<MouseWheel>", self._on_hand_wheel)

    def _on_hand_wheel(self, event: tk.Event) -> None:
        self.hand_canvas.yview_scroll(int(-event.delta / 120), "units")

    @staticmethod
    def _show_error(message: str) -> None:
        messagebox.showerror("操作失败", message)
