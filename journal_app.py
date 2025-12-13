import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime


# ==========================
# DATABASE LAYER
# ==========================

class JournalDatabase:
    def __init__(self, db_name="journal.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                mood TEXT,
                q1 TEXT,
                q2 TEXT,
                q3 TEXT,
                advice TEXT
            )
            """
        )
        self.conn.commit()

    def add_entry(self, date, mood, q1, q2, q3, advice):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO entries (date, mood, q1, q2, q3, advice)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (date, mood, q1, q2, q3, advice),
        )
        self.conn.commit()

    def get_all_entries(self):
        """Return list of (id, date, mood) sorted newest first."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, date, mood FROM entries ORDER BY id DESC"
        )
        return cursor.fetchall()

    def get_entry(self, entry_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        return cursor.fetchone()


# ==========================
# ADVICE / MOOD LOGIC
# ==========================

def generate_advice(mood, text):
    """
    Very simple "personalized" advice based on mood and keywords
    in the combined journal text.
    """
    text_lower = text.lower()

    mood_based = {
        "Very Happy": "You seem to be in a really good place today. Take a moment to appreciate what’s going well and think about how you can keep that going.",
        "Happy": "You’re feeling pretty good today. Try to note the small things that made you feel this way so you can revisit them on tougher days.",
        "Neutral": "You’re feeling neutral. That’s okay. Maybe pick one small thing you’re grateful for or something you’re looking forward to.",
        "Sad": "You’re feeling sad today. Be gentle with yourself—try to do one kind thing for yourself and maybe reach out to someone you trust.",
        "Very Sad": "You’re really down right now. It might help to talk to a close friend, family member, or a professional. You don’t have to carry everything alone.",
        "Stressed": "You’re feeling stressed. Try to break your tasks into smaller steps, and give yourself permission to rest between them.",
        "Anxious": "You’re feeling anxious. Slow, deep breaths and grounding yourself in the present moment can help. Focus on what you can control right now.",
        "Not specified": "You didn’t choose a mood, but your writing still matters. You’re taking time to understand yourself—that’s already a big step."
    }

    advice = mood_based.get(mood, mood_based["Not specified"])

    # Keyword tweaks to make it feel more personalized
    if "tired" in text_lower or "exhausted" in text_lower:
        advice += "\n\nYou mentioned feeling tired. Try to prioritize rest tonight, even if it’s just going to bed a bit earlier or taking a short break."
    if "overwhelmed" in text_lower or "too much" in text_lower:
        advice += "\n\nFeeling overwhelmed is a signal to slow down. Break things into tiny steps and tackle them one at a time."
    if "lonely" in text_lower or "alone" in text_lower:
        advice += "\n\nYou also mentioned feeling alone. Consider reaching out to someone you trust or doing something comforting that makes you feel connected."
    if "proud" in text_lower or "accomplished" in text_lower:
        advice += "\n\nYou noticed something you’re proud of—celebrate that! Acknowledge your progress instead of skipping past it."

    return advice


# ==========================
# GUI LAYER
# ==========================

class JournalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reflective Journal")
        self.root.geometry("900x600")

        self.db = JournalDatabase()

        # Main notebook (tabs)
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.entry_frame = ttk.Frame(notebook)
        self.history_frame = ttk.Frame(notebook)

        notebook.add(self.entry_frame, text="Today's Entry")
        notebook.add(self.history_frame, text="Past Entries")

        # Build UI for each tab
        self.build_entry_tab()
        self.build_history_tab()

        # Load existing entries into the list
        self.load_entries_list()

        # Simple reminder loop (for demo: every 60 seconds)
        # Change 60 * 1000 to 60 * 60 * 1000 for hourly, etc.
        self.schedule_reminder()

    # ---------- Reminder logic ----------
    def schedule_reminder(self):
        self.root.after(60 * 1000, self.show_reminder_popup)

    def show_reminder_popup(self):
        messagebox.showinfo(
            "Reminder",
            "Take a moment to journal your thoughts today 💭"
        )
        # Reschedule the next reminder
        self.schedule_reminder()

    # ---------- Today's Entry Tab ----------
    def build_entry_tab(self):
        # Top section: date and mood
        top_frame = ttk.Frame(self.entry_frame)
        top_frame.pack(fill="x", pady=10)

        today_str = datetime.now().strftime("%Y-%m-%d")
        ttk.Label(top_frame, text=f"Date: {today_str}", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        ttk.Label(top_frame, text="Mood:", font=("Arial", 11)).pack(side="left", padx=(40, 5))

        self.mood_var = tk.StringVar()
        mood_options = [
            "Very Happy", "Happy", "Neutral",
            "Sad", "Very Sad", "Stressed", "Anxious"
        ]
        self.mood_var.set("Neutral")
        mood_menu = ttk.Combobox(top_frame, textvariable=self.mood_var, values=mood_options, state="readonly", width=15)
        mood_menu.pack(side="left")

        # Middle section: 3 guided questions
        self.questions = [
            "1. What are you feeling right now?",
            "2. What is something that went well today?",
            "3. Is there anything bothering you at the moment?",
        ]

        self.answer_texts = []

        questions_frame = ttk.Frame(self.entry_frame)
        questions_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for i, q in enumerate(self.questions):
            q_label = ttk.Label(questions_frame, text=q, font=("Arial", 11, "bold"))
            q_label.pack(anchor="w", pady=(5, 0))

            text_widget = tk.Text(questions_frame, height=4, wrap="word")
            text_widget.pack(fill="x", pady=(0, 10))
            self.answer_texts.append(text_widget)

        # Save button
        button_frame = ttk.Frame(self.entry_frame)
        button_frame.pack(pady=5)

        save_button = ttk.Button(button_frame, text="Save Entry", command=self.save_entry)
        save_button.pack()

        # Advice display
        advice_frame = ttk.LabelFrame(self.entry_frame, text="Personalized Advice", padding=10)
        advice_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.advice_text = tk.Text(advice_frame, height=6, wrap="word", state="disabled")
        self.advice_text.pack(fill="both", expand=True)

    def save_entry(self):
        date_str = datetime.now().strftime("%Y-%m-%d")
        mood = self.mood_var.get() or "Not specified"

        answers = []
        for text_widget in self.answer_texts:
            content = text_widget.get("1.0", "end").strip()
            answers.append(content)

        # Check if the user actually wrote something
        if all(ans == "" for ans in answers):
            messagebox.showwarning(
                "Empty Entry",
                "Please write something in at least one of the questions before saving."
            )
            return

        combined_text = " ".join(answers)
        advice = generate_advice(mood, combined_text)

        # Save to database
        self.db.add_entry(date_str, mood, answers[0], answers[1], answers[2], advice)

        # Show advice in the GUI
        self.advice_text.config(state="normal")
        self.advice_text.delete("1.0", "end")
        self.advice_text.insert("1.0", advice)
        self.advice_text.config(state="disabled")

        # Clear the text boxes
        for text_widget in self.answer_texts:
            text_widget.delete("1.0", "end")

        messagebox.showinfo("Saved", "Your journal entry has been saved.")
        # Reload history list
        self.load_entries_list()

    # ---------- Past Entries Tab ----------
    def build_history_tab(self):
        # Left side: list of entries
        left_frame = ttk.Frame(self.history_frame)
        left_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)

        ttk.Label(left_frame, text="Entries", font=("Arial", 11, "bold")).pack(anchor="w")

        self.entries_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.entries_listbox.pack(side="left", fill="y", pady=5)

        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.entries_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.entries_listbox.config(yscrollcommand=scrollbar.set)

        self.entries_listbox.bind("<<ListboxSelect>>", self.on_entry_select)

        # Right side: details of selected entry
        right_frame = ttk.Frame(self.history_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        ttk.Label(right_frame, text="Entry Details", font=("Arial", 11, "bold")).pack(anchor="w")

        self.detail_text = tk.Text(right_frame, wrap="word", state="disabled")
        self.detail_text.pack(fill="both", expand=True, pady=5)

        # For mapping listbox index to entry IDs
        self.entries_metadata = []

    def load_entries_list(self):
        self.entries_listbox.delete(0, "end")
        self.entries_metadata = self.db.get_all_entries()

        for entry in self.entries_metadata:
            entry_id, date_str, mood = entry
            display_text = f"{date_str} - {mood}"
            self.entries_listbox.insert("end", display_text)

    def on_entry_select(self, event):
        if not self.entries_listbox.curselection():
            return

        index = self.entries_listbox.curselection()[0]
        entry_id = self.entries_metadata[index][0]

        entry = self.db.get_entry(entry_id)
        if not entry:
            return

        # entry = (id, date, mood, q1, q2, q3, advice)
        _, date_str, mood, q1, q2, q3, advice = entry

        details = (
            f"Date: {date_str}\n"
            f"Mood: {mood}\n\n"
            f"{self.questions[0]}\n{q1}\n\n"
            f"{self.questions[1]}\n{q2}\n\n"
            f"{self.questions[2]}\n{q3}\n\n"
            f"Advice:\n{advice}"
        )

        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", details)
        self.detail_text.config(state="disabled")


# ==========================
# MAIN
# ==========================

def main():
    root = tk.Tk()
    app = JournalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
