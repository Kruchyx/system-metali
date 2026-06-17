import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import backend


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Metale szlachetne - 3.0")
        self.root.geometry("1500x820")
        self.root.minsize(1200, 720)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        backend.load_portfolio()
        self.snapshot = backend.get_market_snapshot()

        self.dark_mode = False
        self.chart_canvas = None

        self.build_ui()
        self.refresh()
        self.root.after(500, self.show_api_warning_if_needed)

    # =========================
    # UI GŁÓWNE
    # =========================
    def build_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.top_bar = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text="System analizy inwestycji w metale szlachetne",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=14, sticky="w")

        self.theme_switch = ctk.CTkSwitch(
            self.top_bar,
            text="Tryb ciemny",
            command=self.toggle_theme
        )
        self.theme_switch.grid(row=0, column=1, padx=20, pady=14, sticky="e")

        self.tabs = ctk.CTkTabview(self.root, corner_radius=12)
        self.tabs.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        self.portfolio_tab = self.tabs.add("Portfel")
        self.add_tab = self.tabs.add("Dodaj transakcję")
        self.market_tab = self.tabs.add("Kursy")
        self.charts_tab = self.tabs.add("Wykresy")
        self.history_tab = self.tabs.add("Historia cen")
        self.education_tab = self.tabs.add("Edukacja")

        self.build_portfolio_tab()
        self.build_add_tab()
        self.build_market_tab()
        self.build_charts_tab()
        self.build_history_tab()
        self.build_education_tab()

    # =========================
    # PORTFEL
    # =========================
    def build_portfolio_tab(self):
        self.portfolio_tab.grid_columnconfigure(0, weight=1)
        self.portfolio_tab.grid_rowconfigure(2, weight=1)

        self.cards_frame = ctk.CTkFrame(self.portfolio_tab, corner_radius=16)
        self.cards_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")

        for i in range(4):
            self.cards_frame.grid_columnconfigure(i, weight=1)

        self.card_purchase = self.create_card(self.cards_frame, "Wartość zakupu", "0.00 PLN")
        self.card_current = self.create_card(self.cards_frame, "Wartość aktualna", "0.00 PLN")
        self.card_profit = self.create_card(self.cards_frame, "Zysk / strata", "0.00 PLN")
        self.card_roi = self.create_card(self.cards_frame, "Stopa zwrotu", "0.00 %")

        self.card_purchase.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.card_current.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.card_profit.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        self.card_roi.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        self.action_frame = ctk.CTkFrame(self.portfolio_tab, corner_radius=16)
        self.action_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")

        self.refresh_button = ctk.CTkButton(
            self.action_frame,
            text="Odśwież wycenę",
            width=170,
            command=self.refresh_market
        )
        self.refresh_button.pack(side="left", padx=12, pady=12)

        self.delete_button = ctk.CTkButton(
            self.action_frame,
            text="Usuń zaznaczoną",
            width=170,
            fg_color="#c62828",
            hover_color="#8e1b1b",
            command=self.delete
        )
        self.delete_button.pack(side="left", padx=6, pady=12)

        self.table_container = ctk.CTkFrame(self.portfolio_tab, corner_radius=16)
        self.table_container.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.table_container.grid_columnconfigure(0, weight=1)
        self.table_container.grid_rowconfigure(0, weight=1)

        columns = (
            "id", "data", "metal", "kg", "oz",
            "purchase_price", "current_price",
            "purchase_value", "current_value",
            "profit", "roi"
        )

        self.tree = ttk.Treeview(self.table_container, columns=columns, show="headings")

        headings = {
            "id": "ID",
            "data": "Data",
            "metal": "Metal",
            "kg": "Ilość [kg]",
            "oz": "Ilość [oz]",
            "purchase_price": "Cena zakupu [PLN/oz]",
            "current_price": "Cena aktualna [PLN/oz]",
            "purchase_value": "Wartość zakupu [PLN]",
            "current_value": "Wartość aktualna [PLN]",
            "profit": "Zysk/strata [PLN]",
            "roi": "Stopa zwrotu [%]",
        }

        widths = {
            "id": 50,
            "data": 105,
            "metal": 90,
            "kg": 105,
            "oz": 105,
            "purchase_price": 160,
            "current_price": 160,
            "purchase_value": 165,
            "current_value": 165,
            "profit": 140,
            "roi": 130,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            anchor = "center" if col in ("id", "data", "metal") else "e"
            self.tree.column(col, width=widths[col], anchor=anchor)

        y_scroll = ttk.Scrollbar(self.table_container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(self.table_container, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=(12, 0))
        y_scroll.grid(row=0, column=1, sticky="ns", pady=(12, 0), padx=(0, 12))
        x_scroll.grid(row=1, column=0, sticky="ew", padx=(12, 0), pady=(0, 12))

    def create_card(self, parent, title, value):
        frame = ctk.CTkFrame(parent, corner_radius=14)
        frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=13),
            text_color=("gray25", "gray75")
        )
        title_label.grid(row=0, column=0, padx=18, pady=(15, 4), sticky="w")

        value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=22, weight="bold")
        )
        value_label.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="w")

        frame.title_label = title_label
        frame.value_label = value_label
        return frame

    # =========================
    # DODAWANIE TRANSAKCJI
    # =========================
    def build_add_tab(self):
        self.add_tab.grid_columnconfigure(0, weight=1)
        self.add_tab.grid_rowconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(self.add_tab, corner_radius=18)
        wrapper.grid(row=0, column=0, padx=25, pady=25, sticky="n")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            wrapper,
            text="Dodawanie nowej transakcji",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, padx=30, pady=(30, 20), sticky="w")

        self.metal = tk.StringVar(value="zloto")
        self.amount = ctk.CTkEntry(wrapper, width=260, placeholder_text="np. 1")
        self.unit = tk.StringVar(value="kg")
        self.price = ctk.CTkEntry(wrapper, width=260, placeholder_text="np. 4800")
        self.price_unit = tk.StringVar(value="kg")
        self.currency = tk.StringVar(value="pln")

        self.add_form_row(wrapper, 1, "Metal", ctk.CTkComboBox(wrapper, variable=self.metal, values=["zloto", "srebro"], width=260))
        self.add_form_row(wrapper, 2, "Ilość", self.amount)
        self.add_form_row(wrapper, 3, "Jednostka ilości", ctk.CTkComboBox(wrapper, variable=self.unit, values=["kg", "oz"], width=260))
        self.add_form_row(wrapper, 4, "Cena zakupu", self.price)
        self.add_form_row(wrapper, 5, "Jednostka ceny", ctk.CTkComboBox(wrapper, variable=self.price_unit, values=["kg", "oz"], width=260))
        self.add_form_row(wrapper, 6, "Waluta ceny zakupu", ctk.CTkComboBox(wrapper, variable=self.currency, values=["pln", "usd"], width=260))

        add_button = ctk.CTkButton(
            wrapper,
            text="Dodaj transakcję",
            height=40,
            command=self.add
        )
        add_button.grid(row=7, column=0, columnspan=2, padx=30, pady=(25, 10), sticky="ew")

        clear_button = ctk.CTkButton(
            wrapper,
            text="Wyczyść formularz",
            height=40,
            fg_color="gray45",
            hover_color="gray35",
            command=self.clear_form
        )
        clear_button.grid(row=8, column=0, columnspan=2, padx=30, pady=(0, 30), sticky="ew")

    def add_form_row(self, parent, row, label_text, widget):
        label = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.grid(row=row, column=0, padx=(30, 15), pady=10, sticky="w")
        widget.grid(row=row, column=1, padx=(15, 30), pady=10, sticky="e")

    # =========================
    # KURSY
    # =========================
    def build_market_tab(self):
        self.market_tab.grid_columnconfigure(0, weight=1)
        self.market_tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.market_tab, corner_radius=16)
        header.grid(row=0, column=0, padx=25, pady=(25, 12), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Aktualne dane rynkowe",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=22, pady=18, sticky="w")

        market_box = ctk.CTkFrame(self.market_tab, corner_radius=16)
        market_box.grid(row=1, column=0, padx=25, pady=(0, 12), sticky="nsew")
        market_box.grid_columnconfigure(0, weight=1)
        market_box.grid_rowconfigure(0, weight=1)

        self.market_text = ctk.CTkTextbox(
            market_box,
            font=ctk.CTkFont(family="Consolas", size=15),
            corner_radius=12
        )
        self.market_text.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")

        button_frame = ctk.CTkFrame(self.market_tab, corner_radius=16)
        button_frame.grid(row=2, column=0, padx=25, pady=(0, 25), sticky="ew")

        ctk.CTkButton(
            button_frame,
            text="Odśwież kursy",
            width=170,
            height=38,
            command=self.refresh_market
        ).pack(side="left", padx=14, pady=14)

    # =========================
    # WYKRESY
    # =========================
    def build_charts_tab(self):
        self.charts_tab.grid_columnconfigure(0, weight=1)
        self.charts_tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.charts_tab, corner_radius=16)
        header.grid(row=0, column=0, padx=25, pady=(25, 12), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Wykresy portfela",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=22, pady=18, sticky="w")

        ctk.CTkButton(
            header,
            text="Odśwież wykresy",
            width=170,
            command=self.refresh_charts
        ).grid(row=0, column=1, padx=22, pady=18, sticky="e")

        self.chart_frame = ctk.CTkFrame(self.charts_tab, corner_radius=16)
        self.chart_frame.grid(row=1, column=0, padx=25, pady=(0, 25), sticky="nsew")

    # =========================
    # HISTORIA CEN
    # =========================
    def build_history_tab(self):
        self.history_tab.grid_columnconfigure(0, weight=1)
        self.history_tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.history_tab, corner_radius=16)
        header.grid(row=0, column=0, padx=25, pady=(25, 12), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Historia cen metali",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=22, pady=18, sticky="w")

        ctk.CTkButton(
            header,
            text="Odśwież historię",
            width=170,
            command=self.refresh_history_chart
        ).grid(row=0, column=1, padx=22, pady=18, sticky="e")

        self.history_frame = ctk.CTkFrame(self.history_tab, corner_radius=16)
        self.history_frame.grid(row=1, column=0, padx=25, pady=(0, 25), sticky="nsew")

    # =========================
    # EDUKACJA
    # =========================
    def build_education_tab(self):
        self.education_tab.grid_columnconfigure(0, weight=1)
        self.education_tab.grid_rowconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(self.education_tab, corner_radius=16)
        wrapper.grid(row=0, column=0, padx=25, pady=25, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            wrapper,
            text="Moduł edukacyjny",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=22, pady=(22, 10), sticky="w")

        text = ctk.CTkTextbox(
            wrapper,
            wrap="word",
            font=ctk.CTkFont(size=15),
            corner_radius=12
        )
        text.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")

        content = """Złoto i srebro są metalami szlachetnymi, które mogą pełnić funkcję zabezpieczenia kapitału. Ich ceny zależą między innymi od sytuacji gospodarczej, kursu dolara amerykańskiego, inflacji oraz popytu inwestycyjnego i przemysłowego.

Podstawowe zasady inwestowania:

1. Dywersyfikacja
Nie warto lokować całego kapitału w jeden instrument. Metale szlachetne mogą być częścią portfela, ale nie powinny być jego jedynym składnikiem.

2. Ryzyko kursowe
Ceny złota i srebra najczęściej są podawane w USD, dlatego dla inwestora w Polsce ważny jest również kurs USD/PLN.

3. Jednostki
Cena rynkowa metali jest zwykle podawana za uncję trojańską, natomiast zakup fizyczny często odbywa się w gramach lub kilogramach.

4. Różnica między ceną giełdową a detaliczną
Cena zakupu fizycznego metalu może być wyższa od ceny rynkowej ze względu na marżę sprzedawcy, koszty produkcji, transportu lub podatki.

5. Długoterminowy charakter inwestycji
Metale szlachetne często traktowane są jako inwestycja długoterminowa, a nie narzędzie do krótkoterminowej spekulacji.
"""
        text.insert("1.0", content)
        text.configure(state="disabled")

    # =========================
    # AKCJE
    # =========================
    # =========================
    # KOMUNIKAT API
    # =========================
    def show_api_warning_if_needed(self):
        if not backend.has_api_key():
            messagebox.showwarning(
                "Brak klucza API",
                "Nie znaleziono pliku KluczApi.json lub klucz API jest pusty.\n\n"
                "Aplikacja będzie działać, ale nie będzie pobierać aktualnych kursów.\n"
                "Aby włączyć pobieranie danych rynkowych, utwórz plik KluczApi.json "
                "w folderze aplikacji i wpisz własny klucz GoldAPI."
            )

    def add(self):
        try:
            amount = self._parse_decimal(self.amount.get())
            price = self._parse_decimal(self.price.get())

            backend.add_transaction(
                datetime.now().strftime("%Y-%m-%d"),
                self.metal.get(),
                amount,
                self.unit.get(),
                price,
                self.price_unit.get(),
                self.currency.get(),
            )

            self.clear_form()
            self.snapshot = backend.get_market_snapshot()
            self.refresh()
            self.tabs.set("Portfel")
            messagebox.showinfo("Sukces", "Transakcja została dodana.")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def delete(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning("Uwaga", "Wybierz transakcję do usunięcia.")
            return

        if not messagebox.askyesno("Potwierdzenie", "Czy na pewno usunąć zaznaczoną transakcję?"):
            return

        item = self.tree.item(selected[0])
        index = int(item["values"][0]) - 1

        try:
            backend.delete_transaction(index)
            self.refresh()
            messagebox.showinfo("Sukces", "Transakcja została usunięta.")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def refresh_market(self):
        if not backend.has_api_key():
            self.snapshot = backend.get_market_snapshot()
            self.refresh()
            messagebox.showwarning(
                "Brak klucza API",
                "Do pobierania kursów wymagany jest plik KluczApi.json z poprawnym kluczem GoldAPI.\n\n"
                "Utwórz plik KluczApi.json w folderze aplikacji i wpisz w nim:\n"
                "{\n    \"gold_api_key\": \"TWÓJ_KLUCZ_API\"\n}"
            )
            return

        self.snapshot = backend.get_market_snapshot()
        self.refresh()
        messagebox.showinfo("Informacja", "Dane rynkowe zostały odświeżone.")

    def clear_form(self):
        self.amount.delete(0, tk.END)
        self.price.delete(0, tk.END)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = backend.get_portfolio_rows(self.snapshot)
        for row in rows:
            self.tree.insert("", "end", values=row)

        purchase, current, profit = backend.calculate_summary(self.snapshot)

        roi = Decimal("0")
        if purchase > 0:
            roi = (profit / purchase) * Decimal("100")

        self.card_purchase.value_label.configure(text=f"{backend.fmt2(purchase)} PLN")
        self.card_current.value_label.configure(text=f"{backend.fmt2(current)} PLN")
        self.card_profit.value_label.configure(text=f"{backend.fmt2(profit)} PLN")
        self.card_roi.value_label.configure(text=f"{backend.fmt2(roi)} %")

        if profit > 0:
            self.card_profit.value_label.configure(text_color="#2ecc71")
        elif profit < 0:
            self.card_profit.value_label.configure(text_color="#e74c3c")
        else:
            self.card_profit.value_label.configure(text_color=("black", "white"))

        self.refresh_market_text()

        if hasattr(self, "chart_frame"):
            self.refresh_charts()

        if hasattr(self, "history_frame"):
            self.refresh_history_chart()

        self.apply_tree_style()

    def refresh_market_text(self):
        if not backend.has_api_key():
            lines = [
                "BRAK KLUCZA API",
                "",
                "Do pobierania kursów wymagany jest plik KluczApi.json.",
                "",
                "Utwórz plik KluczApi.json w folderze aplikacji i wpisz:",
                "",
                "{",
                '    "gold_api_key": "TWÓJ_KLUCZ_API"',
                "}",
                "",
                "Bez klucza aplikacja nie pobiera kursów z GoldAPI, TradingView ani NBP.",
            ]

            self.market_text.configure(state="normal")
            self.market_text.delete("1.0", tk.END)
            self.market_text.insert("1.0", "\n".join(lines))
            self.market_text.configure(state="disabled")
            return

        usd_pln = self.snapshot.get("usd_pln")
        silver_usd = self.snapshot.get("silver_usd_oz")
        gold_usd = self.snapshot.get("gold_usd_oz")

        silver_pln = backend.get_current_price_pln_oz("srebro", self.snapshot)
        gold_pln = backend.get_current_price_pln_oz("zloto", self.snapshot)

        lines = [
            "AKTUALNE DANE RYNKOWE",
            "",
            f"Status API: {self.snapshot.get('api_message', 'brak informacji')}",
            "",
            f"Kurs USD/PLN: {backend.fmt4(usd_pln) if usd_pln else 'brak'}",
            "",
            "SREBRO",
            f"USD/oz: {backend.fmt2(silver_usd) if silver_usd else 'brak'}",
            f"PLN/oz: {backend.fmt2(silver_pln) if silver_pln else 'brak'}",
            "",
            "ZŁOTO",
            f"USD/oz: {backend.fmt2(gold_usd) if gold_usd else 'brak'}",
            f"PLN/oz: {backend.fmt2(gold_pln) if gold_pln else 'brak'}",
        ]

        self.market_text.configure(state="normal")
        self.market_text.delete("1.0", tk.END)
        self.market_text.insert("1.0", "\n".join(lines))
        self.market_text.configure(state="disabled")

    def refresh_charts(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        rows = backend.get_portfolio_rows(self.snapshot)

        if not rows:
            label = ctk.CTkLabel(
                self.chart_frame,
                text="Brak danych do wyświetlenia wykresów.",
                font=ctk.CTkFont(size=16)
            )
            label.pack(pady=40)
            return

        labels = []
        purchase_values = []
        current_values = []
        profits = []

        for row in rows:
            labels.append(f"{row[0]} - {row[2]}")
            purchase_values.append(float(row[7]))
            current_values.append(float(row[8]))
            profits.append(float(row[9]))

        is_dark = ctk.get_appearance_mode().lower() == "dark"

        fig = Figure(figsize=(12, 5), dpi=100)
        fig.patch.set_facecolor("#1f1f1f" if is_dark else "#ffffff")

        ax1 = fig.add_subplot(121)
        x = range(len(labels))
        ax1.bar([i - 0.2 for i in x], purchase_values, width=0.4, label="Wartość zakupu")
        ax1.bar([i + 0.2 for i in x], current_values, width=0.4, label="Wartość aktualna")
        ax1.set_title("Wartość zakupu vs wartość aktualna")
        ax1.set_ylabel("PLN")
        ax1.set_xticks(list(x))
        ax1.set_xticklabels(labels, rotation=45, ha="right")
        ax1.legend()

        ax2 = fig.add_subplot(122)
        ax2.bar(labels, profits)
        ax2.set_title("Zysk / strata według transakcji")
        ax2.set_ylabel("PLN")
        ax2.tick_params(axis="x", rotation=45)

        if is_dark:
            for ax in [ax1, ax2]:
                ax.set_facecolor("#2b2b2b")
                ax.tick_params(colors="white")
                ax.title.set_color("white")
                ax.yaxis.label.set_color("white")
                ax.xaxis.label.set_color("white")
                for spine in ax.spines.values():
                    spine.set_color("white")
                legend = ax.get_legend()
                if legend:
                    legend.get_frame().set_facecolor("#2b2b2b")
                    for text in legend.get_texts():
                        text.set_color("white")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=16, pady=16)

    def refresh_history_chart(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        gold_history = backend.get_market_history("zloto")
        silver_history = backend.get_market_history("srebro")

        if not gold_history and not silver_history:
            label = ctk.CTkLabel(
                self.history_frame,
                text="Brak zapisanych danych historycznych. Kliknij kilka razy 'Odśwież kursy', aby zebrać dane.",
                font=ctk.CTkFont(size=16)
            )
            label.pack(pady=40)
            return

        is_dark = ctk.get_appearance_mode().lower() == "dark"

        fig = Figure(figsize=(12, 5), dpi=100)
        fig.patch.set_facecolor("#1f1f1f" if is_dark else "#ffffff")

        ax = fig.add_subplot(111)

        if gold_history:
            ax.plot(
                range(len(gold_history)),
                [float(row[1]) for row in gold_history],
                marker="o",
                label="Złoto"
            )

        if silver_history:
            ax.plot(
                range(len(silver_history)),
                [float(row[1]) for row in silver_history],
                marker="o",
                label="Srebro"
            )

        ax.set_title("Historia cen metali")
        ax.set_ylabel("Cena [PLN/oz]")
        ax.set_xlabel("Kolejne zapisane odczyty")
        ax.legend()
        ax.grid(True, alpha=0.3)

        if is_dark:
            ax.set_facecolor("#2b2b2b")
            ax.tick_params(colors="white")
            ax.title.set_color("white")
            ax.yaxis.label.set_color("white")
            ax.xaxis.label.set_color("white")
            for spine in ax.spines.values():
                spine.set_color("white")
            legend = ax.get_legend()
            if legend:
                legend.get_frame().set_facecolor("#2b2b2b")
                for text in legend.get_texts():
                    text.set_color("white")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.history_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=16, pady=16)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        ctk.set_appearance_mode("dark" if self.dark_mode else "light")
        self.theme_switch.configure(text="Tryb jasny" if self.dark_mode else "Tryb ciemny")
        self.apply_tree_style()
        self.refresh_charts()

    def apply_tree_style(self):
        is_dark = ctk.get_appearance_mode().lower() == "dark"

        style = ttk.Style()
        style.theme_use("default")

        if is_dark:
            tree_bg = "#242424"
            tree_fg = "#ffffff"
            heading_bg = "#1f1f1f"
            selected_bg = "#1f6aa5"
        else:
            tree_bg = "#ffffff"
            tree_fg = "#000000"
            heading_bg = "#e9e9e9"
            selected_bg = "#1f6aa5"

        style.configure(
            "Treeview",
            background=tree_bg,
            foreground=tree_fg,
            fieldbackground=tree_bg,
            rowheight=28,
            borderwidth=0
        )

        style.configure(
            "Treeview.Heading",
            background=heading_bg,
            foreground=tree_fg,
            font=("Arial", 10, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", selected_bg)],
            foreground=[("selected", "#ffffff")]
        )

    @staticmethod
    def _parse_decimal(value: str) -> Decimal:
        try:
            parsed = Decimal(value.strip().replace(",", "."))
            if parsed <= 0:
                raise ValueError("Wartość musi być większa od 0.")
            return parsed
        except (InvalidOperation, AttributeError):
            raise ValueError("Wpisz poprawną liczbę.")


if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()
