# -*- coding: utf-8 -*-
"""
아주대의료원신협 내부용 예금 특판 갈아타기 상담 계산기 v5
- Python 표준 라이브러리만 사용(tkinter)
- 직원/조합원 상담용 UI
- 기존 만기일까지 공정비교 + 특판 만기까지 참고수익 별도 표시
- 세율: 일반과세 15.4%, 세금우대 1.4%, 비과세 0%, 직접입력
- 손익분기 특판금리, 100만원/1천만원당 추가수익
- 상담결과 TXT 저장 및 인쇄용 결과 복사

실행:
  python deposit_switch_calculator_internal_v5.py

EXE 빌드 권장:
  python -m PyInstaller --onedir --windowed --clean --name "예금특판갈아타기계산기" deposit_switch_calculator_internal_v5.py

주의:
  상담 참고용 단순 계산기입니다. 실제 지급이자는 상품 약관, 중도해지 구간별 이율,
  세금우대/비과세 한도, 원단위 절사 기준 등에 따라 달라질 수 있습니다.
"""

import calendar
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
from pathlib import Path

DATE_FMT = "%Y-%m-%d"
ORG_NAME = "아주대의료원신협"
APP_TITLE = "예금 특판 갈아타기 상담 계산기"


def parse_float(value: str, field_name: str) -> float:
    value = value.replace(',', '').strip()
    if value == '':
        raise ValueError(f'{field_name}을(를) 입력해 주세요.')
    try:
        return float(value)
    except ValueError:
        raise ValueError(f'{field_name}은(는) 숫자로 입력해 주세요.')


def parse_date(value: str, field_name: str) -> date:
    value = value.strip().replace('.', '-').replace('/', '-')
    if value == '':
        raise ValueError(f'{field_name}을(를) 입력해 주세요.')
    try:
        return datetime.strptime(value, DATE_FMT).date()
    except ValueError:
        raise ValueError(f'{field_name}은(는) YYYY-MM-DD 형식으로 입력해 주세요. 예: 2026-06-15')


def add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def simple_interest(principal: float, annual_rate_percent: float, days: int) -> float:
    if days <= 0:
        return 0.0
    return principal * (annual_rate_percent / 100.0) * (days / 365.0)


def won(n: float) -> str:
    return f'{round(n):,}원'


def pct(n: float) -> str:
    return f'{n:.3f}%'


class DatePicker(tk.Toplevel):
    def __init__(self, master, target_entry: ttk.Entry, start_date: date | None = None, on_pick=None):
        super().__init__(master)
        self.target_entry = target_entry
        self.on_pick = on_pick
        self.selected = start_date or date.today()
        self.year = self.selected.year
        self.month = self.selected.month
        self.title('날짜 선택')
        self.resizable(False, False)
        self.configure(bg='white')
        self.transient(master)
        self.grab_set()

        self.header = ttk.Frame(self, padding=(10, 8))
        self.header.pack(fill='x')
        ttk.Button(self.header, text='‹', width=3, command=self.prev_month).pack(side='left')
        self.title_label = ttk.Label(self.header, text='', font=('Malgun Gothic', 11, 'bold'), anchor='center')
        self.title_label.pack(side='left', expand=True, fill='x', padx=8)
        ttk.Button(self.header, text='›', width=3, command=self.next_month).pack(side='right')

        self.days_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        self.days_frame.pack()
        self.draw_calendar()

        x = master.winfo_pointerx() - 120
        y = master.winfo_pointery() + 10
        self.geometry(f'+{max(20, x)}+{max(20, y)}')

    def prev_month(self):
        self.month = 12 if self.month == 1 else self.month - 1
        if self.month == 12:
            self.year -= 1
        self.draw_calendar()

    def next_month(self):
        self.month = 1 if self.month == 12 else self.month + 1
        if self.month == 1:
            self.year += 1
        self.draw_calendar()

    def pick(self, day: int):
        picked = date(self.year, self.month, day)
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, picked.strftime(DATE_FMT))
        if self.on_pick:
            self.on_pick()
        self.destroy()

    def draw_calendar(self):
        for w in self.days_frame.winfo_children():
            w.destroy()
        self.title_label.configure(text=f'{self.year}년 {self.month}월')
        for c, name in enumerate(['월', '화', '수', '목', '금', '토', '일']):
            ttk.Label(self.days_frame, text=name, width=4, anchor='center', font=('Malgun Gothic', 9, 'bold')).grid(row=0, column=c, pady=3)
        cal = calendar.Calendar(firstweekday=0)
        for r, week in enumerate(cal.monthdayscalendar(self.year, self.month), start=1):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.days_frame, text='', width=4).grid(row=r, column=c, padx=1, pady=1)
                else:
                    ttk.Button(self.days_frame, text=str(day), width=4, command=lambda d=day: self.pick(d)).grid(row=r, column=c, padx=1, pady=1)


class DepositSwitchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'{ORG_NAME} {APP_TITLE} v5')
        self.geometry('1180x850')
        self.minsize(1080, 780)
        self.configure(bg='#eef4fb')
        self.last_result = ''
        self.create_style()
        self.create_widgets()
        self.reset(clear_result=False)

    def create_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('App.TFrame', background='#eef4fb')
        style.configure('Card.TFrame', background='white', relief='flat')
        style.configure('Soft.TFrame', background='#f8fafc', relief='flat')
        style.configure('Title.TLabel', background='#eef4fb', font=('Malgun Gothic', 22, 'bold'), foreground='#0f2742')
        style.configure('Sub.TLabel', background='#eef4fb', font=('Malgun Gothic', 10), foreground='#52677e')
        style.configure('Card.TLabel', background='white', font=('Malgun Gothic', 10))
        style.configure('Header.TLabel', background='white', font=('Malgun Gothic', 13, 'bold'), foreground='#0f2742')
        style.configure('Metric.TLabel', background='#f8fafc', font=('Malgun Gothic', 11, 'bold'), foreground='#1d4ed8')
        style.configure('Good.TLabel', background='white', font=('Malgun Gothic', 17, 'bold'), foreground='#047857')
        style.configure('Bad.TLabel', background='white', font=('Malgun Gothic', 17, 'bold'), foreground='#b91c1c')
        style.configure('Neutral.TLabel', background='white', font=('Malgun Gothic', 16, 'bold'), foreground='#1e3a8a')
        style.configure('TButton', font=('Malgun Gothic', 10), padding=7)
        style.configure('Accent.TButton', font=('Malgun Gothic', 11, 'bold'), padding=10)
        style.configure('TRadiobutton', background='white', font=('Malgun Gothic', 10))
        style.configure('TCheckbutton', background='white', font=('Malgun Gothic', 10))

    def create_widgets(self):
        outer = ttk.Frame(self, style='App.TFrame', padding=22)
        outer.pack(fill='both', expand=True)

        ttk.Label(outer, text=f'{ORG_NAME} {APP_TITLE}', style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text='기존 만기일까지 공정 비교하고, 특판 만기까지의 추가 참고수익은 별도로 표시합니다.', style='Sub.TLabel').pack(anchor='w', pady=(5, 14))

        grid = ttk.Frame(outer, style='App.TFrame')
        grid.pack(fill='both', expand=True)
        grid.columnconfigure(0, weight=0)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(1, weight=1)

        left = ttk.Frame(grid, style='App.TFrame')
        left.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=(0, 12))
        right = ttk.Frame(grid, style='App.TFrame')
        right.grid(row=0, column=1, rowspan=2, sticky='nsew')
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        self.entries = {}
        self._money_card(left)
        self._date_card(left)
        self._option_card(left)
        self._period_card(right)
        self._result_card(right)
        self._buttons(outer)

        note = '※ 상담 참고용 단순 계산입니다. 실제 지급이자는 상품 약관, 중도해지 구간별 이율, 세금우대/비과세 한도, 원단위 절사 기준 등에 따라 달라질 수 있습니다.'
        ttk.Label(outer, text=note, style='Sub.TLabel', wraplength=1100).pack(anchor='w', pady=(8, 0))

    def _money_card(self, parent):
        card = ttk.Frame(parent, style='Card.TFrame', padding=18)
        card.pack(fill='x', pady=(0, 12))
        ttk.Label(card, text='① 금액 및 이율', style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 12))
        fields = [
            ('principal', '예치금액', '100,000,000', '원'),
            ('old_rate', '기존 약정이율', '3.40', '%'),
            ('early_rate', '중도해지 이율', '1.00', '%'),
            ('special_rate', '특판 이율', '3.80', '%'),
        ]
        for i, (key, label, default, unit) in enumerate(fields, start=1):
            ttk.Label(card, text=label, style='Card.TLabel').grid(row=i, column=0, sticky='w', pady=6)
            ent = ttk.Entry(card, font=('Malgun Gothic', 11), width=22)
            ent.insert(0, default)
            ent.grid(row=i, column=1, sticky='we', padx=8, pady=6)
            ttk.Label(card, text=unit, style='Card.TLabel').grid(row=i, column=2, sticky='w')
            self.entries[key] = ent
        card.columnconfigure(1, weight=1)

    def _date_card(self, parent):
        card = ttk.Frame(parent, style='Card.TFrame', padding=18)
        card.pack(fill='x', pady=(0, 12))
        ttk.Label(card, text='② 날짜 선택', style='Header.TLabel').grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 12))
        labels = [
            ('old_start', '기존 예치일'),
            ('old_maturity', '기존 만기일'),
            ('switch_date', '중도해지/특판 재예치일'),
            ('special_maturity', '특판 만기일'),
        ]
        for i, (key, label) in enumerate(labels, start=1):
            ttk.Label(card, text=label, style='Card.TLabel').grid(row=i, column=0, sticky='w', pady=6)
            ent = ttk.Entry(card, font=('Malgun Gothic', 11), width=16)
            ent.grid(row=i, column=1, sticky='we', padx=7, pady=6)
            ttk.Button(card, text='선택', width=6, command=lambda e=ent: self.open_picker(e)).grid(row=i, column=2, padx=(0, 3))
            ttk.Button(card, text='오늘', width=6, command=lambda e=ent: self.set_today(e)).grid(row=i, column=3)
            ent.bind('<FocusOut>', lambda _e: self.update_period_preview())
            self.entries[key] = ent
        quick = ttk.Frame(card, style='Card.TFrame')
        quick.grid(row=5, column=0, columnspan=4, sticky='we', pady=(8, 0))
        ttk.Label(quick, text='특판기간', style='Card.TLabel').pack(side='left', padx=(0, 8))
        for m in (6, 12, 24, 36):
            ttk.Button(quick, text=f'{m}개월', command=lambda mm=m: self.set_special_months(mm)).pack(side='left', padx=2)
        ttk.Button(quick, text='기존만기와 맞춤', command=self.match_special_to_old_maturity).pack(side='left', padx=2)
        card.columnconfigure(1, weight=1)

    def _option_card(self, parent):
        card = ttk.Frame(parent, style='Card.TFrame', padding=18)
        card.pack(fill='x')
        ttk.Label(card, text='③ 세금 및 상담옵션', style='Header.TLabel').pack(anchor='w', pady=(0, 8))
        self.tax_mode = tk.StringVar(value='normal')
        tax_rows = [
            ('normal', '일반과세 15.4%', 15.4),
            ('prefer', '세금우대 1.4%', 1.4),
            ('free', '비과세 0%', 0.0),
            ('custom', '직접입력', None),
        ]
        for val, text, rate in tax_rows:
            ttk.Radiobutton(card, text=text, variable=self.tax_mode, value=val, command=self.on_tax_change).pack(anchor='w', pady=2)
        row = ttk.Frame(card, style='Card.TFrame')
        row.pack(fill='x', pady=(5, 0))
        ttk.Label(row, text='직접입력 세율', style='Card.TLabel').pack(side='left')
        self.entries['tax_rate'] = ttk.Entry(row, font=('Malgun Gothic', 10), width=8)
        self.entries['tax_rate'].insert(0, '15.4')
        self.entries['tax_rate'].pack(side='left', padx=8)
        ttk.Label(row, text='%', style='Card.TLabel').pack(side='left')
        self.fair_compare = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text='기본 비교는 기존 만기일까지 공정비교', variable=self.fair_compare).pack(anchor='w', pady=(10, 2))

    def _period_card(self, parent):
        card = ttk.Frame(parent, style='Card.TFrame', padding=18)
        card.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        ttk.Label(card, text='자동 계산 기간', style='Header.TLabel').pack(anchor='w')
        self.period_preview = ttk.Label(card, text='', style='Metric.TLabel', justify='left', padding=12)
        self.period_preview.pack(fill='x', pady=(10, 0))

    def _result_card(self, parent):
        card = ttk.Frame(parent, style='Card.TFrame', padding=18)
        card.grid(row=1, column=0, sticky='nsew')
        ttk.Label(card, text='계산 결과', style='Header.TLabel').pack(anchor='w')
        self.summary_label = ttk.Label(card, text='입력 후 [계산하기]를 눌러주세요.', style='Neutral.TLabel')
        self.summary_label.pack(anchor='w', pady=(10, 8))
        self.result_text = tk.Text(card, height=25, wrap='word', font=('Malgun Gothic', 10), bg='white', relief='flat', padx=8, pady=8)
        self.result_text.pack(fill='both', expand=True)
        self.result_text.configure(state='disabled')

    def _buttons(self, parent):
        buttons = ttk.Frame(parent, style='App.TFrame')
        buttons.pack(fill='x', pady=(14, 4))
        ttk.Button(buttons, text='계산하기', command=self.calculate, style='Accent.TButton').pack(side='left')
        ttk.Button(buttons, text='결과 복사', command=self.copy_result).pack(side='left', padx=6)
        ttk.Button(buttons, text='TXT 저장', command=self.save_txt).pack(side='left', padx=6)
        ttk.Button(buttons, text='기간 다시 계산', command=self.update_period_preview).pack(side='left', padx=6)
        ttk.Button(buttons, text='초기화', command=self.reset).pack(side='left', padx=6)

    def on_tax_change(self):
        mapping = {'normal': '15.4', 'prefer': '1.4', 'free': '0.0'}
        mode = self.tax_mode.get()
        if mode in mapping:
            self.entries['tax_rate'].delete(0, tk.END)
            self.entries['tax_rate'].insert(0, mapping[mode])

    def open_picker(self, entry):
        try:
            current = parse_date(entry.get(), '날짜')
        except ValueError:
            current = date.today()
        DatePicker(self, entry, current, self.update_period_preview)

    def set_today(self, entry):
        entry.delete(0, tk.END)
        entry.insert(0, date.today().strftime(DATE_FMT))
        self.update_period_preview()

    def set_special_months(self, months: int):
        try:
            sw = parse_date(self.entries['switch_date'].get(), '중도해지/특판 재예치일')
        except ValueError as e:
            messagebox.showwarning('날짜 확인', str(e))
            return
        self.entries['special_maturity'].delete(0, tk.END)
        self.entries['special_maturity'].insert(0, add_months(sw, months).strftime(DATE_FMT))
        self.update_period_preview()

    def match_special_to_old_maturity(self):
        self.entries['special_maturity'].delete(0, tk.END)
        self.entries['special_maturity'].insert(0, self.entries['old_maturity'].get())
        self.update_period_preview()

    def get_periods(self):
        old_start = parse_date(self.entries['old_start'].get(), '기존 예치일')
        old_maturity = parse_date(self.entries['old_maturity'].get(), '기존 만기일')
        switch_date = parse_date(self.entries['switch_date'].get(), '중도해지/특판 재예치일')
        special_maturity = parse_date(self.entries['special_maturity'].get(), '특판 만기일')
        if not old_start < old_maturity:
            raise ValueError('기존 만기일은 기존 예치일보다 뒤여야 합니다.')
        if not old_start <= switch_date <= old_maturity:
            raise ValueError('중도해지일은 기존 예치일과 기존 만기일 사이여야 합니다.')
        if not switch_date < special_maturity:
            raise ValueError('특판 만기일은 특판 재예치일보다 뒤여야 합니다.')
        total_days = (old_maturity - old_start).days
        elapsed_days = (switch_date - old_start).days
        remaining_days = (old_maturity - switch_date).days
        special_days = (special_maturity - switch_date).days
        fair_days = min(remaining_days, special_days)
        extra_days = max(0, special_days - remaining_days)
        return old_start, old_maturity, switch_date, special_maturity, total_days, elapsed_days, remaining_days, special_days, fair_days, extra_days

    def update_period_preview(self):
        try:
            old_start, old_maturity, switch_date, special_maturity, total_days, elapsed_days, remaining_days, special_days, fair_days, extra_days = self.get_periods()
            txt = (
                f'기존 전체 예치기간: {total_days:,}일  ({old_start} ~ {old_maturity})\n'
                f'현재까지 경과기간: {elapsed_days:,}일\n'
                f'기존 잔여기간: {remaining_days:,}일\n'
                f'특판 전체 예치기간: {special_days:,}일  ({switch_date} ~ {special_maturity})\n'
                f'공정 비교 적용기간: {fair_days:,}일\n'
                f'특판 만기가 더 길어 추가로 발생하는 참고기간: {extra_days:,}일'
            )
            self.period_preview.configure(text=txt)
        except Exception as e:
            self.period_preview.configure(text=f'날짜 확인 필요: {e}')

    def reset(self, clear_result=True):
        today = date.today()
        defaults = {
            'principal': '100,000,000',
            'old_rate': '3.40',
            'early_rate': '1.00',
            'special_rate': '3.80',
            'tax_rate': '15.4',
            'old_start': add_months(today, -4).strftime(DATE_FMT),
            'old_maturity': add_months(today, 8).strftime(DATE_FMT),
            'switch_date': today.strftime(DATE_FMT),
            'special_maturity': add_months(today, 12).strftime(DATE_FMT),
        }
        for key, value in defaults.items():
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, value)
        self.tax_mode.set('normal')
        self.fair_compare.set(True)
        if clear_result:
            self.set_result('입력 후 [계산하기]를 눌러주세요.', '', None)
        self.update_period_preview()

    def calculate(self):
        try:
            principal = parse_float(self.entries['principal'].get(), '예치금액')
            old_rate = parse_float(self.entries['old_rate'].get(), '기존 약정이율')
            early_rate = parse_float(self.entries['early_rate'].get(), '중도해지 이율')
            special_rate = parse_float(self.entries['special_rate'].get(), '특판 이율')
            tax_rate = parse_float(self.entries['tax_rate'].get(), '세율')
            if principal <= 0:
                raise ValueError('예치금액은 0보다 커야 합니다.')
            if min(old_rate, early_rate, special_rate, tax_rate) < 0:
                raise ValueError('이율과 세율은 음수로 입력할 수 없습니다.')
            old_start, old_maturity, switch_date, special_maturity, total_days, elapsed_days, remaining_days, special_days, fair_days, extra_days = self.get_periods()
            self.update_period_preview()
            tax = tax_rate / 100.0

            # 전체 상담 지표
            old_full = simple_interest(principal, old_rate, total_days)
            old_elapsed_contract = simple_interest(principal, old_rate, elapsed_days)
            old_remaining = simple_interest(principal, old_rate, remaining_days)
            early_interest = simple_interest(principal, early_rate, elapsed_days)
            early_loss = old_elapsed_contract - early_interest

            # 공정비교: 오늘부터 기존 만기일까지의 동일 기간만 비교
            fair_keep = old_remaining
            fair_switch = simple_interest(principal, special_rate, fair_days)
            fair_gross_gain = fair_switch - fair_keep - early_loss
            fair_net_gain = fair_gross_gain * (1 - tax)

            # 참고: 특판 만기까지 모두 보유하는 경우
            special_full = simple_interest(principal, special_rate, special_days)
            extra_special = simple_interest(principal, special_rate, extra_days)
            full_switch_total = early_interest + special_full
            full_keep_to_old_maturity = old_full
            full_gross_gain = full_switch_total - full_keep_to_old_maturity
            full_net_gain = full_gross_gain * (1 - tax)

            # 손익분기: 경과기간 손실까지 회복하려면 공정비교 기간 동안 필요한 특판금리
            if fair_days > 0:
                needed_interest = fair_keep + early_loss
                breakeven_rate = (needed_interest / principal) * (365.0 / fair_days) * 100.0
            else:
                breakeven_rate = 0.0

            per_million = fair_net_gain / (principal / 1_000_000)
            per_10million = fair_net_gain / (principal / 10_000_000)
            decision = '갈아타기 유리 예상' if fair_net_gain > 0 else '기존 유지 유리 예상' if fair_net_gain < 0 else '손익 동일 예상'

            body = []
            body.append(f'[{ORG_NAME}] {APP_TITLE} 상담결과')
            body.append(f'계산일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            body.append('')
            body.append('■ 상담 결론')
            body.append(f'  - {decision}')
            body.append(f'  - 기존 만기일까지 공정비교 세후 예상 차익: {won(fair_net_gain)}')
            body.append(f'  - 100만원당 세후 예상 차익: {won(per_million)}')
            body.append(f'  - 1천만원당 세후 예상 차익: {won(per_10million)}')
            body.append(f'  - 손익분기 특판금리: 연 {pct(breakeven_rate)}')
            body.append('')
            body.append('■ 입력 조건')
            body.append(f'  - 예치금액: {won(principal)}')
            body.append(f'  - 기존 약정이율: 연 {pct(old_rate)}')
            body.append(f'  - 중도해지 이율: 연 {pct(early_rate)}')
            body.append(f'  - 특판 이율: 연 {pct(special_rate)}')
            body.append(f'  - 적용 세율: {tax_rate:.2f}%')
            body.append('')
            body.append('■ 날짜 및 기간')
            body.append(f'  - 기존 예치일: {old_start}')
            body.append(f'  - 기존 만기일: {old_maturity}')
            body.append(f'  - 중도해지/특판 재예치일: {switch_date}')
            body.append(f'  - 특판 만기일: {special_maturity}')
            body.append(f'  - 기존 전체 예치기간: {total_days:,}일')
            body.append(f'  - 현재까지 경과기간: {elapsed_days:,}일')
            body.append(f'  - 기존 잔여기간: {remaining_days:,}일')
            body.append(f'  - 특판 전체 예치기간: {special_days:,}일')
            body.append(f'  - 공정 비교 적용기간: {fair_days:,}일')
            body.append(f'  - 특판 추가 참고기간: {extra_days:,}일')
            body.append('')
            body.append('■ 기존 예금을 유지하는 경우')
            body.append(f'  - 기존 만기까지 전체 약정이자 세전: {won(old_full)} / 세후: {won(old_full * (1-tax))}')
            body.append(f'  - 오늘부터 기존 만기일까지 잔여기간 이자 세전: {won(old_remaining)} / 세후: {won(old_remaining * (1-tax))}')
            body.append('')
            body.append('■ 중도해지 후 특판 가입하는 경우')
            body.append(f'  - 경과기간 기존 약정이자 상당액 세전: {won(old_elapsed_contract)}')
            body.append(f'  - 중도해지 실제 적용이자 세전: {won(early_interest)}')
            body.append(f'  - 중도해지로 포기하는 이자 세전: {won(early_loss)} / 세후: {won(early_loss * (1-tax))}')
            body.append(f'  - 기존 만기일까지 특판 이자 세전: {won(fair_switch)} / 세후: {won(fair_switch * (1-tax))}')
            body.append('')
            body.append('■ 공정비교 결과: 기존 만기일까지')
            body.append(f'  - 기준: 특판 만기가 기존 만기보다 길어도 기존 만기일까지 동일 기간만 비교')
            body.append(f'  - 기존 유지 잔여이자 세전: {won(fair_keep)}')
            body.append(f'  - 갈아타기 특판이자 세전: {won(fair_switch)}')
            body.append(f'  - 차감: 중도해지로 포기하는 경과기간 이자 세전: {won(early_loss)}')
            body.append(f'  - 세전 예상 차익: {won(fair_gross_gain)}')
            body.append(f'  - 세후 예상 차익: {won(fair_net_gain)}')
            body.append('')
            body.append('■ 참고: 특판 만기까지 모두 보유하는 경우')
            body.append(f'  - 특판 전체 예상이자 세전: {won(special_full)} / 세후: {won(special_full * (1-tax))}')
            body.append(f'  - 기존 만기 이후 추가 참고기간 이자 세전: {won(extra_special)} / 세후: {won(extra_special * (1-tax))}')
            body.append(f'  - 중도해지이자 + 특판전체이자 기준 세후 차익: {won(full_net_gain)}')
            body.append('')
            body.append('※ 이 계산은 단리·365일·세전 이자에 동일 세율 적용 기준의 상담용 단순 산출입니다.')
            body.append('※ 실제 지급이자는 상품 약관, 중도해지 구간별 이율, 세금우대/비과세 한도, 원단위 절사 기준 등에 따라 달라질 수 있습니다.')

            self.set_result(f'{decision} · 공정비교 세후 예상 차익 {won(fair_net_gain)}', '\n'.join(body), fair_net_gain)
        except ValueError as e:
            messagebox.showwarning('입력 확인', str(e))

    def set_result(self, summary: str, body: str, gain: float | None):
        if gain is None:
            style = 'Neutral.TLabel'
        elif gain > 0:
            style = 'Good.TLabel'
        elif gain < 0:
            style = 'Bad.TLabel'
        else:
            style = 'Neutral.TLabel'
        self.summary_label.configure(style=style, text=summary)
        self.last_result = body
        self.result_text.configure(state='normal')
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, body)
        self.result_text.configure(state='disabled')

    def copy_result(self):
        if not self.last_result.strip():
            messagebox.showinfo('안내', '복사할 계산 결과가 없습니다.')
            return
        self.clipboard_clear()
        self.clipboard_append(self.last_result)
        messagebox.showinfo('복사 완료', '계산 결과가 클립보드에 복사되었습니다.')

    def save_txt(self):
        if not self.last_result.strip():
            messagebox.showinfo('안내', '저장할 계산 결과가 없습니다.')
            return
        default_name = f'예금특판_갈아타기_상담결과_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        path = filedialog.asksaveasfilename(
            title='상담결과 저장',
            defaultextension='.txt',
            initialfile=default_name,
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        if not path:
            return
        Path(path).write_text(self.last_result, encoding='utf-8')
        messagebox.showinfo('저장 완료', f'저장되었습니다.\n{path}')


if __name__ == '__main__':
    app = DepositSwitchApp()
    app.mainloop()
