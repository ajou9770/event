# -*- coding: utf-8 -*-
"""
예금 특판 갈아타기 예상이익 계산기 v4
- 날짜 선택형 UI
- 공정비교 기준일 적용: 기본은 '기존 만기일'까지 동일 기간 비교
- 특판 만기일까지의 추가 이자는 별도 참고 표시
- Python 표준 라이브러리(tkinter)만 사용

실행:
  python special_deposit_switch_calculator_v4.py
"""

import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

TAX_RATE_DEFAULT = 15.4
DATE_FMT = "%Y-%m-%d"


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
    return principal * (annual_rate_percent / 100.0) * (days / 365.0)


def won(n: float) -> str:
    return f'{round(n):,}원'


class DatePicker(tk.Toplevel):
    def __init__(self, master, target_entry: ttk.Entry, start_date: date | None = None):
        super().__init__(master)
        self.target_entry = target_entry
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
        self.title('예금 특판 갈아타기 계산기 v4')
        self.geometry('1080x850')
        self.minsize(1000, 780)
        self.configure(bg='#edf4fb')
        self.create_style()
        self.create_widgets()
        self.update_period_preview()

    def create_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('App.TFrame', background='#edf4fb')
        style.configure('Card.TFrame', background='white')
        style.configure('TLabel', background='#edf4fb', font=('Malgun Gothic', 10))
        style.configure('Card.TLabel', background='white', font=('Malgun Gothic', 10))
        style.configure('Title.TLabel', background='#edf4fb', font=('Malgun Gothic', 22, 'bold'), foreground='#0b2a4a')
        style.configure('Sub.TLabel', background='#edf4fb', font=('Malgun Gothic', 10), foreground='#5d7186')
        style.configure('Header.TLabel', background='white', font=('Malgun Gothic', 13, 'bold'), foreground='#0b2a4a')
        style.configure('Hint.TLabel', background='white', font=('Malgun Gothic', 9), foreground='#64748b')
        style.configure('Metric.TLabel', background='#f8fafc', font=('Malgun Gothic', 11, 'bold'), foreground='#1d4ed8')
        style.configure('Good.TLabel', background='white', font=('Malgun Gothic', 16, 'bold'), foreground='#047857')
        style.configure('Bad.TLabel', background='white', font=('Malgun Gothic', 16, 'bold'), foreground='#b91c1c')
        style.configure('Neutral.TLabel', background='white', font=('Malgun Gothic', 15, 'bold'), foreground='#1e3a8a')
        style.configure('Accent.TButton', font=('Malgun Gothic', 11, 'bold'), padding=10)
        style.configure('TButton', font=('Malgun Gothic', 10), padding=7)
        style.configure('TRadiobutton', background='white', font=('Malgun Gothic', 10))

    def create_widgets(self):
        outer = ttk.Frame(self, style='App.TFrame', padding=24)
        outer.pack(fill='both', expand=True)

        ttk.Label(outer, text='예금 특판 갈아타기 예상이익 계산기', style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text='기본 계산은 기존 만기일까지 동일 기간으로 비교합니다. 특판 만기일까지의 추가 이자는 별도 참고로 표시됩니다.', style='Sub.TLabel').pack(anchor='w', pady=(6, 18))

        grid = ttk.Frame(outer, style='App.TFrame')
        grid.pack(fill='both', expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(1, weight=1)

        money_card = ttk.Frame(grid, style='Card.TFrame', padding=18)
        money_card.grid(row=0, column=0, sticky='nsew', padx=(0, 8), pady=(0, 12))
        date_card = ttk.Frame(grid, style='Card.TFrame', padding=18)
        date_card.grid(row=0, column=1, sticky='nsew', padx=(8, 0), pady=(0, 12))

        ttk.Label(money_card, text='금액 및 이율', style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 12))
        self.entries = {}
        money_fields = [
            ('principal', '예치금액', '100,000,000', '원'),
            ('old_rate', '기존 약정이율', '3.40', '%'),
            ('early_rate', '중도해지 이율', '1.00', '%'),
            ('special_rate', '특판 이율', '3.40', '%'),
            ('tax_rate', '세율', str(TAX_RATE_DEFAULT), '%'),
        ]
        for i, (key, label, default, unit) in enumerate(money_fields, start=1):
            ttk.Label(money_card, text=label, style='Card.TLabel').grid(row=i, column=0, sticky='w', pady=7)
            ent = ttk.Entry(money_card, font=('Malgun Gothic', 11), width=24)
            ent.insert(0, default)
            ent.grid(row=i, column=1, sticky='we', padx=8, pady=7)
            ttk.Label(money_card, text=unit, style='Card.TLabel').grid(row=i, column=2, sticky='w')
            self.entries[key] = ent
        money_card.columnconfigure(1, weight=1)

        ttk.Label(date_card, text='날짜 선택', style='Header.TLabel').grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 12))
        today = date.today()
        defaults = {
            'old_start': add_months(today, -4),
            'old_maturity': add_months(today, 8),
            'switch_date': today,
            'special_maturity': add_months(today, 12),
        }
        for i, (key, label) in enumerate([
            ('old_start', '기존 예치일'),
            ('old_maturity', '기존 만기일'),
            ('switch_date', '중도해지/특판 재예치일'),
            ('special_maturity', '특판 만기일'),
        ], start=1):
            ttk.Label(date_card, text=label, style='Card.TLabel').grid(row=i, column=0, sticky='w', pady=7)
            ent = ttk.Entry(date_card, font=('Malgun Gothic', 11), width=18)
            ent.insert(0, defaults[key].strftime(DATE_FMT))
            ent.grid(row=i, column=1, sticky='we', padx=8, pady=7)
            ttk.Button(date_card, text='선택', width=6, command=lambda e=ent: self.open_picker(e)).grid(row=i, column=2, padx=(0, 4))
            ttk.Button(date_card, text='오늘', width=6, command=lambda e=ent: self.set_today(e)).grid(row=i, column=3)
            ent.bind('<FocusOut>', lambda _e: self.update_period_preview())
            self.entries[key] = ent
        date_card.columnconfigure(1, weight=1)

        quick = ttk.Frame(date_card, style='Card.TFrame')
        quick.grid(row=5, column=0, columnspan=4, sticky='we', pady=(8, 0))
        ttk.Label(quick, text='특판기간 빠른 설정', style='Hint.TLabel').pack(side='left', padx=(0, 8))
        for m in (6, 12, 24, 36):
            ttk.Button(quick, text=f'{m}개월', command=lambda mm=m: self.set_special_months(mm)).pack(side='left', padx=2)

        preview_card = ttk.Frame(grid, style='Card.TFrame', padding=18)
        preview_card.grid(row=1, column=0, sticky='nsew', padx=(0, 8))
        ttk.Label(preview_card, text='자동 계산 기간', style='Header.TLabel').pack(anchor='w', pady=(0, 12))
        self.period_preview = ttk.Label(preview_card, text='', style='Metric.TLabel', justify='left', padding=12)
        self.period_preview.pack(fill='x')

        option = ttk.Frame(preview_card, style='Card.TFrame')
        option.pack(fill='x', pady=(16, 0))
        ttk.Label(option, text='비교 방식', style='Header.TLabel').pack(anchor='w', pady=(0, 8))
        self.compare_mode = tk.StringVar(value='fair')
        ttk.Radiobutton(option, text='권장: 기존 만기일까지 공정비교', variable=self.compare_mode, value='fair').pack(anchor='w', pady=3)
        ttk.Radiobutton(option, text='참고: 특판 만기일까지 전체 수령액 비교', variable=self.compare_mode, value='special_full').pack(anchor='w', pady=3)
        ttk.Label(option, text='※ 특판 만기가 기존 만기보다 늦으면 전체 수령액은 기간이 길어져 커질 수 있습니다.', style='Hint.TLabel', wraplength=430).pack(anchor='w', pady=(8, 0))

        result_card = ttk.Frame(grid, style='Card.TFrame', padding=18)
        result_card.grid(row=1, column=1, sticky='nsew', padx=(8, 0))
        ttk.Label(result_card, text='계산 결과', style='Header.TLabel').pack(anchor='w')
        self.summary_label = ttk.Label(result_card, text='입력 후 [계산하기]를 눌러주세요.', style='Neutral.TLabel')
        self.summary_label.pack(anchor='w', pady=(12, 8))
        self.result_text = tk.Text(result_card, height=22, wrap='word', font=('Malgun Gothic', 10), bg='white', relief='flat', padx=8, pady=8)
        self.result_text.pack(fill='both', expand=True)
        self.result_text.configure(state='disabled')

        buttons = ttk.Frame(outer, style='App.TFrame')
        buttons.pack(fill='x', pady=(16, 8))
        ttk.Button(buttons, text='계산하기', command=self.calculate, style='Accent.TButton').pack(side='left')
        ttk.Button(buttons, text='기간 다시 계산', command=self.update_period_preview).pack(side='left', padx=8)
        ttk.Button(buttons, text='초기화', command=self.reset).pack(side='left')

        note = '※ 상담 참고용 단순 계산입니다. 실제 지급이자는 상품 약관, 세금우대/비과세, 중도해지 구간별 이율, 원단위 절사 기준 등에 따라 달라질 수 있습니다.'
        ttk.Label(outer, text=note, style='Sub.TLabel', wraplength=1000).pack(anchor='w')

    def open_picker(self, entry):
        try:
            current = parse_date(entry.get(), '날짜')
        except ValueError:
            current = date.today()
        DatePicker(self, entry, current)
        self.after(300, self.update_period_preview)

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
        mat = add_months(sw, months)
        self.entries['special_maturity'].delete(0, tk.END)
        self.entries['special_maturity'].insert(0, mat.strftime(DATE_FMT))
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
        fair_special_days = min(remaining_days, special_days)
        extra_special_days = max(0, special_days - remaining_days)
        return old_start, old_maturity, switch_date, special_maturity, total_days, elapsed_days, remaining_days, special_days, fair_special_days, extra_special_days

    def update_period_preview(self):
        try:
            old_start, old_maturity, switch_date, special_maturity, total_days, elapsed_days, remaining_days, special_days, fair_days, extra_days = self.get_periods()
            txt = (
                f'기존 예치기간: {total_days:,}일  ({old_start} ~ {old_maturity})\n'
                f'현재 경과기간: {elapsed_days:,}일\n'
                f'기존 잔여기간: {remaining_days:,}일\n'
                f'특판 예치기간: {special_days:,}일  ({switch_date} ~ {special_maturity})\n'
                f'공정비교 대상 특판기간: {fair_days:,}일\n'
                f'특판 추가기간: {extra_days:,}일'
            )
            self.period_preview.configure(text=txt)
        except Exception as e:
            self.period_preview.configure(text=f'날짜 확인 필요: {e}')

    def reset(self):
        today = date.today()
        defaults = {
            'principal': '100,000,000',
            'old_rate': '3.40',
            'early_rate': '1.00',
            'special_rate': '3.40',
            'tax_rate': str(TAX_RATE_DEFAULT),
            'old_start': add_months(today, -4).strftime(DATE_FMT),
            'old_maturity': add_months(today, 8).strftime(DATE_FMT),
            'switch_date': today.strftime(DATE_FMT),
            'special_maturity': add_months(today, 12).strftime(DATE_FMT),
        }
        for k, v in defaults.items():
            self.entries[k].delete(0, tk.END)
            self.entries[k].insert(0, v)
        self.compare_mode.set('fair')
        self.set_result('입력 후 [계산하기]를 눌러주세요.', '')
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

            old_start, old_maturity, switch_date, special_maturity, total_days, elapsed_days, remaining_days, special_days, fair_special_days, extra_special_days = self.get_periods()
            self.update_period_preview()

            tax = tax_rate / 100.0
            old_elapsed_contract = simple_interest(principal, old_rate, elapsed_days)
            old_remaining_interest = simple_interest(principal, old_rate, remaining_days)
            old_total_interest = old_elapsed_contract + old_remaining_interest
            early_cancel_interest = simple_interest(principal, early_rate, elapsed_days)
            early_loss = old_elapsed_contract - early_cancel_interest

            special_fair_interest = simple_interest(principal, special_rate, fair_special_days)
            special_full_interest = simple_interest(principal, special_rate, special_days)
            special_extra_interest = simple_interest(principal, special_rate, extra_special_days)

            mode = self.compare_mode.get()
            if mode == 'special_full':
                keep_interest = old_total_interest
                switch_interest = early_cancel_interest + special_full_interest
                compare_title = '특판 만기일까지 전체 수령액 비교'
                compare_desc = '기존 예금 만기유지 이자와 중도해지 이자 + 특판 만기까지 이자를 비교합니다. 단, 기간이 다르면 공정한 금리 비교가 아닐 수 있습니다.'
            else:
                keep_interest = old_total_interest
                switch_interest = early_cancel_interest + special_fair_interest
                compare_title = '기존 만기일까지 공정비교'
                compare_desc = '기존 만기일까지 동일한 종료일 기준으로 비교합니다. 특판 만기가 더 늦어 발생하는 추가 이자는 이익판단에서 제외하고 참고로만 표시합니다.'

            gross_gain = switch_interest - keep_interest
            net_gain = gross_gain * (1 - tax)
            net_keep = keep_interest * (1 - tax)
            net_switch = switch_interest * (1 - tax)

            if fair_special_days > 0:
                required_rate_fair = ((old_total_interest - early_cancel_interest) / principal) * (365.0 / fair_special_days) * 100.0
            else:
                required_rate_fair = 0.0

            if gross_gain > 0:
                decision = '갈아타기 유리 예상'
            elif gross_gain < 0:
                decision = '기존 유지 유리 예상'
            else:
                decision = '손익 동일 예상'

            body = []
            body.append(f'■ 비교 방식: {compare_title}')
            body.append(f'  - {compare_desc}')
            body.append('')
            body.append('■ 핵심 해석')
            body.append(f'  - 중도해지로 포기하는 기존 경과기간 약정이자: {won(early_loss)} / 세후 {won(early_loss * (1 - tax))}')
            body.append(f'  - 기존 만기일까지 특판으로 벌 수 있는 이자: {won(special_fair_interest)}')
            body.append(f'  - 특판 만기까지 추가기간 이자 참고: {won(special_extra_interest)} ({extra_special_days:,}일)')
            body.append('')
            body.append('■ 날짜 및 자동 계산 기간')
            body.append(f'  - 기존 예치일: {old_start}')
            body.append(f'  - 기존 만기일: {old_maturity}')
            body.append(f'  - 중도해지/특판 재예치일: {switch_date}')
            body.append(f'  - 특판 만기일: {special_maturity}')
            body.append(f'  - 기존 전체 예치기간: {total_days:,}일')
            body.append(f'  - 현재까지 경과기간: {elapsed_days:,}일')
            body.append(f'  - 기존 잔여기간: {remaining_days:,}일')
            body.append(f'  - 특판 전체 예치기간: {special_days:,}일')
            body.append(f'  - 공정비교 대상 특판기간: {fair_special_days:,}일')
            body.append('')
            body.append('■ 입력 이율')
            body.append(f'  - 예치금액: {won(principal)}')
            body.append(f'  - 기존 약정이율: 연 {old_rate:.3f}%')
            body.append(f'  - 중도해지 이율: 연 {early_rate:.3f}%')
            body.append(f'  - 특판 이율: 연 {special_rate:.3f}%')
            body.append(f'  - 세율: {tax_rate:.2f}%')
            body.append('')
            body.append('■ 세전 이자')
            body.append(f'  - 기존 만기유지 전체 약정이자: {won(old_total_interest)}')
            body.append(f'  - 경과기간 기존 약정이자 상당액: {won(old_elapsed_contract)}')
            body.append(f'  - 지금 중도해지 시 이자: {won(early_cancel_interest)}')
            body.append(f'  - 기존 잔여기간 이자 상당액: {won(old_remaining_interest)}')
            body.append(f'  - 특판 이자, 공정비교 대상기간: {won(special_fair_interest)}')
            body.append(f'  - 특판 이자, 만기까지 전체: {won(special_full_interest)}')
            body.append('')
            body.append('■ 비교 결과')
            body.append(f'  - 기존 유지 기준 이자: {won(keep_interest)} / 세후 {won(net_keep)}')
            body.append(f'  - 갈아타기 기준 이자: {won(switch_interest)} / 세후 {won(net_switch)}')
            body.append(f'  - 세전 예상 차익: {won(gross_gain)}')
            body.append(f'  - 세후 예상 차익: {won(net_gain)}')
            body.append('')
            body.append('■ 손익분기 특판이율')
            body.append(f'  - 기존 만기일까지 손익분기 특판이율: 연 {required_rate_fair:.3f}%')
            body.append('')
            body.append('※ 단리·365일 기준 단순 계산입니다. 특판 만기가 기존 만기보다 늦은 경우 추가기간 이자는 별도 참고로 보아야 합니다.')

            self.set_result(f'{decision} · 세후 예상 차익 {won(net_gain)}', '\n'.join(body), net_gain)
        except ValueError as e:
            messagebox.showwarning('입력 확인', str(e))

    def set_result(self, summary: str, body: str, gain: float | None = None):
        if gain is not None and gain > 0:
            style = 'Good.TLabel'
        elif gain is not None and gain < 0:
            style = 'Bad.TLabel'
        else:
            style = 'Neutral.TLabel'
        self.summary_label.configure(style=style, text=summary)
        self.result_text.configure(state='normal')
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, body)
        self.result_text.configure(state='disabled')


if __name__ == '__main__':
    app = DepositSwitchApp()
    app.mainloop()
