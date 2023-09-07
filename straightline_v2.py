# -*- coding: utf-8 -*-
"""
Created on Wed Sep  6 11:55:47 2023

@author: Gilberto
"""


import pandas as pd
from datetime import datetime, timedelta

class StraightLineAmortization:
    def __init__(self, settlement_date, maturity_date, first_payment_date, notional_amount, rate, basis_numerator, basis_denominator, amortization_years, payment_frequency):
        self.settlement_date = datetime.strptime(settlement_date, "%m/%d/%Y") if isinstance(settlement_date, str) else settlement_date
        self.maturity_date = datetime.strptime(maturity_date, "%m/%d/%Y") if isinstance(maturity_date, str) else maturity_date
        self.first_payment_date = datetime.strptime(first_payment_date, "%m/%d/%Y") if isinstance(first_payment_date, str) else first_payment_date
        self.notional_amount = notional_amount
        self.rate = rate/100
        self.basis_numerator = basis_numerator
        self.basis_denominator = basis_denominator
        self.amortization_years = amortization_years
        # Add the payment_frequency variable
        self.payment_frequency = payment_frequency
        # Adjust the num_periods and monthly_principal_payment based on payment_frequency
        if self.payment_frequency == "1M":
            self.num_periods = self.amortization_years * 12
        elif self.payment_frequency == "3M":
            self.num_periods = self.amortization_years * 4
        elif self.payment_frequency == "6M":
            self.num_periods = self.amortization_years * 2
        self.period_principal_payment = self.notional_amount / self.num_periods
        
    def compute_days(self, start_date, end_date):
        if self.basis_numerator == "ACT":
            days = (end_date - start_date).days
        else:
            days = 30  # assuming each month has 30 days
        if self.basis_denominator == 360:
            return days
        else:
            return days / 365.0 * 360.0

    def get_next_dates(self, current_date):
        if current_date == self.settlement_date:
            return self.first_payment_date, self.first_payment_date

        # Calculate next_month and next_year based on payment_frequency
        if self.payment_frequency == "1M":
            months_increment = 1
        elif self.payment_frequency == "3M":
            months_increment = 3
        elif self.payment_frequency == "6M":
            months_increment = 6
        
        next_month = (current_date.month + months_increment - 1) % 12 + 1
        next_year = current_date.year + (current_date.month - 1 + months_increment) // 12

        period_end_date = current_date.replace(year=next_year, month=next_month, day=self.first_payment_date.day)

        payment_date = period_end_date
        # If it's a weekend, move to the next business day for payment date
        while payment_date.weekday() >= 5:
            payment_date += timedelta(days=1)

        return period_end_date, payment_date

    def generate_schedule(self):
        data = []
        current_date = self.settlement_date
        payment_number = 1
        notional_amount = self.notional_amount
        
        while current_date < self.maturity_date and payment_number <= self.num_periods:
            period_start_date = current_date
            period_end_date, payment_date = self.get_next_dates(current_date)
            days_in_period = self.compute_days(period_start_date, period_end_date)
            actual_days_in_period = (period_end_date - period_start_date).days
            interest_for_period = (notional_amount * self.rate * days_in_period) / self.basis_denominator
            period_payment = round(interest_for_period + self.period_principal_payment,2)
            notional_amount -= self.period_principal_payment

            data.append([period_start_date, period_end_date, payment_date, payment_number, notional_amount + self.period_principal_payment, period_payment, self.period_principal_payment, actual_days_in_period])

            current_date = period_end_date # Start next period the same day as the previous period's end date
            payment_number += 1

        df = pd.DataFrame(data, columns=['Period Start Date', 'Period End Date', 'Payment Date', 'Payment Number', 'Outstanding Balance', 'Period Payment', 'Principal Payment', 'Actual Days in Period'])
        return df

# Usage
sla = StraightLineAmortization("8/1/2022", "8/1/2032", "9/1/2022", 600000, 7.03, "ACT", 360, 25, "3M")
amortization_schedule = sla.generate_schedule()
print(amortization_schedule)