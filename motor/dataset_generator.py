import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import Workbook

from motor.motor_state import MotorState
from motor.motor_dynamics import update_motor_state


class DatasetGenerator:
    def __init__(self, total_rows=100000, chunk_size=5000, seed=42):
        self.total_rows = total_rows
        self.chunk_size = chunk_size
        self.seed = seed
        random.seed(seed)

    def _initial_state(self):
        return MotorState(
            voltage_v=400.0,
            current_a=0.0,
            speed_rpm=1000.0,
            stator_temp_c=40.0,
            rotor_temp_c=38.0,
            magnet_temp_c=36.0,
            bearing_temp_c=35.0,
            coolant_in_temp_c=25.0,
            coolant_out_temp_c=25.0,
            coolant_flow_rate=1.0,
            coolant_pressure=2.5,
            bearing_health=90.0,
        )

    def _phase_params(self, idx):
        block = idx // 2000
        r = random.Random(self.seed + block)
        phase = block % 6
        if phase == 0:
            return r.uniform(0.25, 0.55), r.uniform(20, 30), 1.0, 0.0
        if phase == 1:
            return r.uniform(0.45, 0.75), r.uniform(22, 35), r.uniform(0.95, 1.0), 0.0
        if phase == 2:
            return r.uniform(0.70, 0.95), r.uniform(25, 40), r.uniform(0.80, 1.0), 0.0
        if phase == 3:
            return r.uniform(0.55, 0.85), r.uniform(28, 42), r.uniform(0.70, 0.95), 0.0
        if phase == 4:
            return r.uniform(0.75, 1.05), r.uniform(30, 45), r.uniform(0.60, 0.90), 0.15
        return r.uniform(0.60, 0.98), r.uniform(24, 38), r.uniform(0.70, 1.0), 0.08

    def _apply_fault_profile(self, state, idx):
        if idx < 20000:
            return state
        if idx < 40000:
            state.bearing_health = max(state.bearing_health - 0.01, 55.0)
            state.vibration_accel += 0.01
        elif idx < 60000:
            state.coolant_flow_rate = max(0.55, state.coolant_flow_rate - 0.00001)
            state.coolant_pressure = max(1.6, state.coolant_pressure - 0.000005)
        elif idx < 80000:
            state.insulation_resistance_mohm = max(60.0, state.insulation_resistance_mohm - 0.02)
            state.partial_discharge += 0.001
        else:
            state.bearing_health = max(35.0, state.bearing_health - 0.02)
            state.coolant_flow_rate = max(0.45, state.coolant_flow_rate - 0.00002)
            state.partial_discharge += 0.002
            state.current_harmonics += 0.01
        return state

    def generate(self, csv_name='motor_dataset_100k.csv', excel_name='motor_dataset_100k.xlsx'):
        motor_folder = Path(__file__).resolve().parent
        csv_path = motor_folder / csv_name
        excel_path = motor_folder / excel_name

        state = self._initial_state()
        start_time = datetime.now()

        wb = Workbook(write_only=True)
        ws = wb.create_sheet(title='motor_data')

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = None
            headers = None

            for i in range(self.total_rows):
                load_fraction, ambient_c, coolant_flow_target, fault_bias = self._phase_params(i)
                state.coolant_flow_rate = 0.90 * state.coolant_flow_rate + 0.10 * coolant_flow_target
                state.coolant_pressure = max(1.5, min(3.0, 2.5 + (state.coolant_flow_rate - 1.0) * 0.5))
                state.coolant_in_temp_c = ambient_c

                load = min(1.2, load_fraction + fault_bias)
                state = update_motor_state(state, load_fraction=load, dt=1.0, ambient_c=ambient_c)
                state = self._apply_fault_profile(state, i)

                row = {
                    'record_id': i + 1,
                    'timestamp': (start_time + timedelta(seconds=i)).isoformat(),
                    'load_fraction': round(load, 4),
                    'ambient_c': round(ambient_c, 2),
                    'voltage_v': round(state.voltage_v, 3),
                    'current_a': round(state.current_a, 3),
                    'speed_rpm': round(state.speed_rpm, 3),
                    'torque_nm': round(state.torque_nm, 3),
                    'power_kw': round(state.power_kw, 3),
                    'efficiency': round(state.efficiency, 5),
                    'back_emf_v': round(state.back_emf_v, 3),
                    'stator_temp_c': round(state.stator_temp_c, 3),
                    'rotor_temp_c': round(state.rotor_temp_c, 3),
                    'magnet_temp_c': round(state.magnet_temp_c, 3),
                    'bearing_temp_c': round(state.bearing_temp_c, 3),
                    'coolant_in_temp_c': round(state.coolant_in_temp_c, 3),
                    'coolant_out_temp_c': round(state.coolant_out_temp_c, 3),
                    'vibration_accel': round(state.vibration_accel, 5),
                    'vibration_vel': round(state.vibration_vel, 5),
                    'coolant_flow_rate': round(state.coolant_flow_rate, 3),
                    'coolant_pressure': round(state.coolant_pressure, 3),
                    'insulation_resistance_mohm': round(state.insulation_resistance_mohm, 3),
                    'partial_discharge': round(state.partial_discharge, 6),
                    'flux_estimate': round(state.flux_estimate, 5),
                    'current_harmonics': round(state.current_harmonics, 5),
                    'stator_health': round(state.stator_health, 3),
                    'rotor_health': round(state.rotor_health, 3),
                    'magnet_health': round(state.magnet_health, 3),
                    'bearing_health': round(state.bearing_health, 3),
                    'cooling_health': round(state.cooling_health, 3),
                    'shaft_health': round(state.shaft_health, 3),
                    'overall_health': round(state.overall_health, 3),
                    'failure_probability': round(state.failure_probability, 5),
                    'rul_hours': round(state.rul_hours, 3),
                    'fault_code': state.fault_code,
                }

                if writer is None:
                    headers = list(row.keys())
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    ws.append(headers)

                writer.writerow(row)
                ws.append([row[h] for h in headers])

        wb.save(excel_path)
        return self.total_rows, csv_path, excel_path


if __name__ == '__main__':
    gen = DatasetGenerator(total_rows=100000, chunk_size=5000, seed=42)
    written, csv_path, excel_path = gen.generate()
    print(f'Saved {written} rows to {csv_path}')
    print(f'Saved Excel file to {excel_path}')