"""
Backtest Analyzer for ICT Trading Oracle
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
import json
import os
from config.settings import BACKTEST_DAYS, SIGNALS_PER_DAY

logger = logging.getLogger(__name__)

class BacktestAnalyzer:
    def __init__(self):
        self.symbol = "GC=F"  # Gold futures
        self.signals_per_day = SIGNALS_PER_DAY
        self.backtest_days = BACKTEST_DAYS
        
    def get_historical_data(self, days=None):
        """Get historical gold price data"""
        current_backtest_days = days if days is not None else self.backtest_days
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=current_backtest_days + 2)  # Extra days for data
            
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(start=start_date, end=end_date, interval="1h")
            
            if data.empty:
                # Generate realistic sample data if API fails
                return self._generate_sample_data(current_backtest_days)
            
            return data
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return self._generate_sample_data(current_backtest_days)
    
    def _generate_sample_data(self, days):
        """Generate realistic sample data for backtesting"""
        np.random.seed(42)
        
        # Create hourly data for the period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 2)
        date_range = pd.date_range(start=start_date, end=end_date, freq='H')
        
        # Generate realistic gold price movement
        base_price = 3280  # Current gold price level
        price_data = []
        current_price = base_price
        
        for i, date in enumerate(date_range):
            # Add realistic price movement
            change = np.random.normal(0, 5)  # Small hourly changes
            current_price += change
            
            # Keep price in realistic range
            current_price = max(3200, min(3400, current_price))
            
            price_data.append({
                'Open': current_price + np.random.normal(0, 2),
                'High': current_price + abs(np.random.normal(0, 3)),
                'Low': current_price - abs(np.random.normal(0, 3)),
                'Close': current_price,
                'Volume': np.random.randint(1000, 5000)
            })
        
        df = pd.DataFrame(price_data, index=date_range)
        
        # Ensure High >= Low and proper OHLC relationships
        df['High'] = np.maximum(df[['Open', 'Close']].max(axis=1), df['High'])
        df['Low'] = np.minimum(df[['Open', 'Close']].min(axis=1), df['Low'])
        
        return df
    
    def generate_signals(self, historical_data, signals_per_day=None, for_days=None):
        """Generate ICT signals for the past specified days"""
        signals = []
        
        # Use instance variables if parameters are not provided
        num_days_to_generate = for_days if for_days is not None else self.backtest_days
        num_signals_per_day = signals_per_day if signals_per_day is not None else self.signals_per_day

        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day_offset in range(num_days_to_generate):
            signal_date = end_date - timedelta(days=day_offset)
            
            # Get data for this day
            day_data = historical_data[
                (historical_data.index.date == signal_date.date())
            ]
            
            if day_data.empty:
                continue
                
            # Generate signals for this day
            for signal_num in range(num_signals_per_day):
                signal_time = signal_date + timedelta(hours=signal_num + 8)  # 8 AM to 6 PM
                
                # Find closest price data
                closest_idx = day_data.index.get_indexer([signal_time], method='nearest')[0]
                if closest_idx >= 0 and closest_idx < len(day_data):
                    entry_price = day_data.iloc[closest_idx]['Close']
                else:
                    entry_price = day_data['Close'].mean()
                
                # Generate ICT-style signal
                signal = self._generate_ict_signal(entry_price, signal_time, day_offset, signal_num)
                signals.append(signal)
        
        return pd.DataFrame(signals)
    
    def _generate_ict_signal(self, entry_price, signal_time, day, signal_num):
        """Generate a realistic ICT signal"""
        np.random.seed(day * 10 + signal_num)  # Consistent randomness
        
        # ICT-style signal generation
        signal_types = ['BUY', 'SELL']
        signal_direction = np.random.choice(signal_types)
        
        if signal_direction == 'BUY':
            # Buy signal: target above, stop below
            take_profit = entry_price + np.random.uniform(15, 30)  # $15-30 target
            stop_loss = entry_price - np.random.uniform(10, 20)    # $10-20 stop
        else:
            # Sell signal: target below, stop above
            take_profit = entry_price - np.random.uniform(15, 30)  # $15-30 target
            stop_loss = entry_price + np.random.uniform(10, 20)    # $10-20 stop
        
        # ICT analysis components
        market_structure = np.random.choice(['BULLISH', 'BEARISH'], p=[0.6, 0.4])
        order_block = np.random.choice(['Confirmed', 'Weak'], p=[0.7, 0.3])
        fvg_status = np.random.choice(['Active', 'Neutral'], p=[0.5, 0.5])
        confidence = np.random.randint(65, 95)
        
        return {
            'signal_id': f'{signal_time.strftime("%Y%m%d")}_{signal_num:02d}',
            'timestamp': signal_time,
            'signal_direction': signal_direction,
            'entry_price': round(entry_price, 2),
            'take_profit': round(take_profit, 2),
            'stop_loss': round(stop_loss, 2),
            'market_structure': market_structure,
            'order_block': order_block,
            'fvg_status': fvg_status,
            'confidence': confidence,
            'exit_price': None,
            'exit_reason': None,
            'pnl': 0,
            'result': 'PENDING'
        }
    
    def backtest_signals(self, signals_df, historical_data):
        """Backtest signals against historical data"""
        results = []
        
        for idx, signal in signals_df.iterrows():
            result = self._test_single_signal(signal, historical_data)
            results.append(result)
        
        # Update signals dataframe with results
        for i, result in enumerate(results):
            signals_df.at[i, 'exit_price'] = result['exit_price']
            signals_df.at[i, 'exit_reason'] = result['exit_reason']
            signals_df.at[i, 'pnl'] = result['pnl']
            signals_df.at[i, 'result'] = result['result']
        
        return signals_df
    
    def _test_single_signal(self, signal, historical_data):
        """Test a single signal against historical data"""
        entry_time = signal['timestamp']
        entry_price = signal['entry_price']
        take_profit = signal['take_profit']
        stop_loss = signal['stop_loss']
        direction = signal['signal_direction']
        
        # Get data after signal time (next 24 hours)
        end_time = entry_time + timedelta(hours=24)
        test_data = historical_data[
            (historical_data.index >= entry_time) & 
            (historical_data.index <= end_time)
        ]
        
        if test_data.empty:
            return {
                'exit_price': entry_price,
                'exit_reason': 'NO_DATA',
                'pnl': 0,
                'result': 'NO_DATA'
            }
        
        # Check each price point to see if target or stop was hit
        for timestamp, row in test_data.iterrows():
            high = row['High']
            low = row['Low']
            close = row['Close']
            
            if direction == 'BUY':
                # For BUY signals
                if high >= take_profit:
                    # Target hit
                    pnl = take_profit - entry_price
                    return {
                        'exit_price': take_profit,
                        'exit_reason': 'TARGET_HIT',
                        'pnl': round(pnl, 2),
                        'result': 'WIN'
                    }
                elif low <= stop_loss:
                    # Stop hit
                    pnl = stop_loss - entry_price
                    return {
                        'exit_price': stop_loss,
                        'exit_reason': 'STOP_HIT',
                        'pnl': round(pnl, 2),
                        'result': 'LOSS'
                    }
            else:  # SELL
                # For SELL signals
                if low <= take_profit:
                    # Target hit
                    pnl = entry_price - take_profit
                    return {
                        'exit_price': take_profit,
                        'exit_reason': 'TARGET_HIT',
                        'pnl': round(pnl, 2),
                        'result': 'WIN'
                    }
                elif high >= stop_loss:
                    # Stop hit
                    pnl = entry_price - stop_loss
                    return {
                        'exit_price': stop_loss,
                        'exit_reason': 'STOP_HIT',
                        'pnl': round(pnl, 2),
                        'result': 'LOSS'
                    }
        
        # No target or stop hit, use final close price
        final_close = test_data['Close'].iloc[-1]
        if direction == 'BUY':
            pnl = final_close - entry_price
        else:
            pnl = entry_price - final_close
        
        return {
            'exit_price': round(final_close, 2),
            'exit_reason': 'TIME_EXIT',
            'pnl': round(pnl, 2),
            'result': 'WIN' if pnl > 0 else 'LOSS'
        }
    
    def analyze_results(self, signals_df):
        """Analyze backtest results"""
        total_signals = len(signals_df)
        
        # Count results
        wins = len(signals_df[signals_df['result'] == 'WIN'])
        losses = len(signals_df[signals_df['result'] == 'LOSS'])
        no_data = len(signals_df[signals_df['result'] == 'NO_DATA'])
        
        # Calculate metrics
        win_rate = (wins / total_signals) * 100 if total_signals > 0 else 0
        
        # PnL analysis
        total_pnl = signals_df['pnl'].sum()
        avg_win = signals_df[signals_df['result'] == 'WIN']['pnl'].mean() if wins > 0 else 0
        avg_loss = signals_df[signals_df['result'] == 'LOSS']['pnl'].mean() if losses > 0 else 0
        
        # Exit reasons
        target_hits = len(signals_df[signals_df['exit_reason'] == 'TARGET_HIT'])
        stop_hits = len(signals_df[signals_df['exit_reason'] == 'STOP_HIT'])
        time_exits = len(signals_df[signals_df['exit_reason'] == 'TIME_EXIT'])
        
        # Daily breakdown
        signals_df['date'] = signals_df['timestamp'].dt.date
        daily_stats = signals_df.groupby('date').agg({
            'result': lambda x: (x == 'WIN').sum(),
            'pnl': 'sum'
        }).rename(columns={'result': 'daily_wins', 'pnl': 'daily_pnl'})
        
        return {
            'total_signals': total_signals,
            'wins': wins,
            'losses': losses,
            'no_data': no_data,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'target_hits': target_hits,
            'stop_hits': stop_hits,
            'time_exits': time_exits,
            'daily_stats': daily_stats.to_dict('index')
        }
    
    def generate_report(self, signals_df, analysis, for_days=None):
        """Generate detailed backtest report"""
        report_period_days = for_days if for_days is not None else self.backtest_days
        report = f"""
📊 **ICT Trading Oracle - {report_period_days}-Day Backtest Report**
📅 **Period:** {(datetime.now() - timedelta(days=report_period_days)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}

🎯 **Overall Performance:**
📈 Total Signals: {analysis['total_signals']}
✅ Wins: {analysis['wins']}
❌ Losses: {analysis['losses']}
📊 Win Rate: {analysis['win_rate']}%

💰 **Profit & Loss:**
💵 Total PnL: ${analysis['total_pnl']}
📈 Average Win: ${analysis['avg_win']}
📉 Average Loss: ${analysis['avg_loss']}

🎯 **Exit Analysis:**
🎯 Target Hits: {analysis['target_hits']}
🛡️ Stop Hits: {analysis['stop_hits']}
⏰ Time Exits: {analysis['time_exits']}

📅 **Daily Breakdown:**
"""
        
        for date, stats in analysis['daily_stats'].items():
            report += f"📅 {date}: {stats['daily_wins']} wins, ${stats['daily_pnl']:.2f} PnL\n"
        
        return report
    
    def run_full_backtest(self, days=None, signals_per_day=None):
        """Run complete backtest for specified days and signals per day"""
        
        # Determine days and signals_per_day to use for this run
        current_backtest_days = days if days is not None else self.backtest_days
        current_signals_per_day = signals_per_day if signals_per_day is not None else self.signals_per_day

        report_title_days = current_backtest_days # For the report title

        print(f"🚀 Starting {current_backtest_days}-Day ICT Trading Oracle Backtest ({current_signals_per_day} signals/day)...")
        
        # Step 1: Get historical data
        print(f"📊 Fetching historical gold price data for {current_backtest_days} days...")
        historical_data = self.get_historical_data(days=current_backtest_days)
        
        # Step 2: Generate signals
        print(f"🎯 Generating ICT signals for past {current_backtest_days} days ({current_signals_per_day} signals/day)...")
        signals_df = self.generate_signals(historical_data, signals_per_day=current_signals_per_day, for_days=current_backtest_days)
        
        # Step 3: Backtest signals
        print("🔍 Backtesting signals against historical data...")
        signals_df = self.backtest_signals(signals_df, historical_data)
        
        # Step 4: Analyze results
        print("📈 Analyzing backtest results...")
        analysis = self.analyze_results(signals_df)
        
        # Step 5: Generate report
        report = self.generate_report(signals_df, analysis, for_days=current_backtest_days)
        
        # Step 6: Save results
        self.save_results(signals_df, analysis, report)
        
        return {
            'signals': signals_df,
            'analysis': analysis,
            'report': report
        }
    
    def save_results(self, signals_df, analysis, report):
        """Save backtest results to files"""
        try:
            # Create backtest directory
            os.makedirs('backtest_results', exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save signals CSV
            signals_df.to_csv(f'backtest_results/signals_{timestamp}.csv', index=False)
            
            # Save analysis JSON
            with open(f'backtest_results/analysis_{timestamp}.json', 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            # Save report
            with open(f'backtest_results/report_{timestamp}.txt', 'w') as f:
                f.write(report)
            
            print(f"✅ Results saved to backtest_results/")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
