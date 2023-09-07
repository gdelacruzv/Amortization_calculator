# -*- coding: utf-8 -*-
"""
Created on Wed Sep  6 12:10:43 2023

@author: Gilberto
"""


import pandas as pd
from datetime import datetime, timedelta

class MortgageStyle:
    def __init__(self, settlement_date, maturity_date, first_payment_date, notional_amount, rate, basis_numerator, basis_denominator, amortization_years, payment_frequency):
        
        if isinstance(settlement_date, str):
            self.settlement_date = datetime.strptime(settlement_date, "%m/%d/%Y")
        else:
            self.settlement_date = datetime.combine(settlement_date, datetime.min.time())
            
        if isinstance(maturity_date, str):
            self.maturity_date = datetime.strptime(maturity_date, "%m/%d/%Y")
        else:
            self.maturity_date = datetime.combine(maturity_date, datetime.min.time())
            
        if isinstance(first_payment_date, str):
            self.first_payment_date = datetime.strptime(first_payment_date, "%m/%d/%Y")
        else:
            self.first_payment_date = datetime.combine(first_payment_date, datetime.min.time())
        
        self.notional_amount = notional_amount
        self.rate = rate / 100
        self.basis_numerator = basis_numerator
        self.basis_denominator = basis_denominator
        self.amortization_years = amortization_years
        self.payment_frequency = payment_frequency
        
        if self.payment_frequency == "1M":
            self.num_periods = self.amortization_years * 12
            standard_period_days = 30
        elif self.payment_frequency == "3M":
            self.num_periods = self.amortization_years * 4
            standard_period_days = 90
        elif self.payment_frequency == "6M":
            self.num_periods = self.amortization_years * 2
            standard_period_days = 180
        
        days_in_first_period = (self.first_payment_date - self.settlement_date).days
        # Check if the days in the first period is less than the standard period days (e.g., 30 for monthly)
        if days_in_first_period < standard_period_days:
            k = standard_period_days
        else:
            k = days_in_first_period
        numerator_factor = 365 if self.basis_numerator == "ACT" else 360
        self.period_payment = round((self.notional_amount + self.notional_amount * (days_in_first_period - k) * self.rate / self.basis_denominator) 
                        * self.rate * numerator_factor / self.basis_denominator / (self.num_periods/self.amortization_years) / (1 - (1 + self.rate * numerator_factor / self.basis_denominator / (self.num_periods/self.amortization_years)) ** (-self.amortization_years * (self.num_periods/self.amortization_years))), 2)

    def _compute_days(self, start_date, end_date):
        if self.basis_numerator == "ACT":
            days = (end_date - start_date).days
        else:
            days = 30  # assuming each month has 30 days
        if self.basis_denominator == 360:
            return days
        else:
            return days / 365.0 * 360.0

    def _get_next_dates(self, current_date):
        if current_date == self.settlement_date:
            return self.first_payment_date, self.first_payment_date
        
        # Determine the month increment based on payment_frequency
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

    def create_mortgage_style_amort(self):
        data = []
        current_date = self.settlement_date
        payment_number = 1
        notional_amount = self.notional_amount

        while current_date < self.maturity_date and payment_number <= self.num_periods:
            period_start_date = current_date
            period_end_date, payment_date = self._get_next_dates(current_date)
            days_in_period = self._compute_days(period_start_date, period_end_date)
            days_in_period = (period_end_date - period_start_date).days
            interest_for_period = (notional_amount * self.rate * days_in_period) / self.basis_denominator
            period_principal_payment = round(self.period_payment - interest_for_period, 2)  # Rounding to the nearest cent here
            notional_amount -= period_principal_payment

            data.append([period_start_date, period_end_date, payment_date, payment_number, notional_amount + period_principal_payment, self.period_payment, period_principal_payment, days_in_period])

            current_date = period_end_date
            payment_number += 1
            
            
        # Convert dates in data list to day, month, and year format
        for row in data:
            row[0] = row[0].strftime('%m/%d/%Y')
            row[1] = row[1].strftime('%m/%d/%Y')
            row[2] = row[2].strftime('%m/%d/%Y')

        
        df = pd.DataFrame(data, columns=["Period Start Date", "Period End Date", "Payment Date", "Payment Number", "Outstanding Balance", "Period Payment", "Principal Payment", "Days in Period"])
        return df

    def create_hybrid_style_amort(self):
        mortgage_df = self.create_mortgage_style_amort()

        # Split the mortgage_df into yearly segments
        dfs = [mortgage_df.iloc[i:i+12] for i in range(0, len(mortgage_df), 12)]

        new_data = []
        notional_amount_reset = self.notional_amount

        for yearly_df in dfs:
            avg_principal_payment = yearly_df['Principal Payment'].mean()
            avg_principal_payment = round(avg_principal_payment, 2)  # Round to 2 decimal places
            for _, row in yearly_df.iterrows():
                interest_for_period = (notional_amount_reset * self.rate * row['Days in Period']) / self.basis_denominator
                period_payment_adjusted = interest_for_period + avg_principal_payment
                notional_amount_reset -= avg_principal_payment

                new_data.append([row['Period Start Date'], row['Period End Date'], row['Payment Date'], row['Payment Number'], notional_amount_reset + avg_principal_payment, period_payment_adjusted, avg_principal_payment, row['Days in Period']])
      
        
        df_new = pd.DataFrame(new_data, columns=["Period Start Date", "Period End Date", "Payment Date", "Payment Number", "Outstanding Balance", "Period Payment", "Principal Payment", "Days in Period"])
        return df_new
    
    
mortgage = MortgageStyle("8/1/2023", "8/1/2032", "9/1/2023", 600000, 7.03, "ACT", 360, 25, payment_frequency="1M")
amortization_schedule = mortgage.create_mortgage_style_amort()
hybrid_schedule = mortgage.create_hybrid_style_amort()
print(amortization_schedule)
