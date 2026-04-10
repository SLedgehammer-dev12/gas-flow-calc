import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Import at top
if 'from controllers import GasFlowController' not in text:
    text = text.replace('from calculations import GasFlowCalculator\n', 'from calculations import GasFlowCalculator\nfrom controllers import GasFlowController\n')

# 2. Add controller initialization
text = text.replace('self.calculator = GasFlowCalculator()', 'self.calculator = GasFlowCalculator()\n        self.controller = GasFlowController()')

# 3. Replace start_calculation
new_start = '''    def start_calculation(self):
        ui_state = self.get_ui_state()
        
        # 1. Gaz Bileşimi Kontrolü
        is_exact, total, mole_fractions, confirmed, error_msg = self.check_gas_composition()
        
        if error_msg:
            messagebox.showerror("Gaz Bileşimi Hatası", error_msg)
            return
        
        if not confirmed:
            return  # Kullanıcı iptal etti
        
        # Normalize bilgisi
        normalization_info = None
        if not is_exact:
            normalization_info = {
                "original_total": total,
                "message": f"Gaz bileşimi %{total:.2f} idi, %100'e normalize edildi."
            }
            self.log_message(f"⚠️ Gaz bileşimi normalize edildi: %{total:.2f} → %100", level="WARNING")

        # 2. Verileri Topla
        inputs, errors = self.controller.prepare_inputs(ui_state, mole_fractions)
        if errors:
            messagebox.showwarning("Giriş Hatası", "\\n".join(errors))
            return
            
        inputs["normalization_info"] = normalization_info

        # 3. Arayüzü Kilitle ve Progress Başlat
        self.is_calculating = True'''

text = re.sub(r'    def start_calculation\(self\):.*?self\.is_calculating = True', new_start, text, flags=re.DOTALL)

# 4. Replace populate_results_table
new_populate = '''    def populate_results_table(self, result):
        # Tabloyu temizle
        for item in self.res_tree.get_children():
            self.res_tree.delete(item)
            
        if not result: return
        
        ui_state = self.get_ui_state()
        rows = self.controller.get_results_table_data(result, self.calc_target.get(), ui_state)
        
        for row in rows:
            if len(row) == 4:
                param, value, unit, tag = row
                self.res_tree.insert("", "end", values=(param, value, unit), tags=(tag,))
            else:
                param, value, unit = row
                self.res_tree.insert("", "end", values=(param, value, unit))

        # Summary Card güncelle
        self._update_summary_card(result, self.calc_target.get())'''

text = re.sub(r'    def populate_results_table\(self, result\):.*?self\._update_summary_card\(result, target\)', new_populate, text, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched main.py successfully')
