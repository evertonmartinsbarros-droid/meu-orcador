import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import tempfile
import os

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTILO
# ==============================================================================
st.set_page_config(page_title="Simulador de Orçamento", page_icon="📊", layout="wide")

st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 26px;
        color: #00CC96;
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        font-size: 16px;
        color: #555;
    }
    .stButton button {
        width: 100%;
        font-weight: bold;
    }
    .stDataFrame {
        border: 1px solid #f0f2f6;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DADOS E ARQUIVOS
# ==============================================================================
FILES = {
    "Materiais": "db_materiais.csv",
    "MaoDeObra": "db_mdo.csv",
    "Kits": "db_kits.csv",
    "Config_Acionamentos": "db_conf_acion.csv",
    "Config_Vasos": "db_conf_vasos.csv",
    "Config_Hidraulica": "db_conf_hidra.csv"
}

DEFAULT_DATA = {
    "Materiais": {
        'ID_Material': [
            'CLP-AUT-01', 'CLP-AUT-02', 'PAINEL-8060', 'PAINEL-10060', 'PAINEL-10080',
            'CONT-MOT-12A', 'RELE-INT-24V', 'DISJ-MOT-10A', 'DISJ-COM-02A', 'BORNE-TERRA',
            'BORNE-SAK-4', 'CANALETA-6040', 'TRILHO-DIN', 'VASO-FIL-3072', 'VASO-FIL-3672',
            'VASO-FIL-4272', 'VASO-FIL-4872', 'VASO-FIL-6380', 'VALV-BORB-E2', 'VALV-BORB-E3',
            'VALV-BORB-E4', 'MEDIA-ZEO-25', 'TUBO-PVC-2', 'CURVA-PVC-90-2', 'TE-PVC-2',
            'LUVA-PVC-2', 'TUBO-PVC-3', 'CURVA-PVC-90-3', 'TE-PVC-3', 'LUVA-PVC-4',
            'TUBO-PVC-4', 'CURVA-PVC-90-4', 'TE-PVC-4', 'BOLSA-FLG-4', 'PARAF-INOX-M10',
            'COLA-AQUA-Tubo', 'ZEO-SUP-34', 'CREPINA-FIL-1', 'IHM-AUT-7POL', 'IHM-AUT-10POL',
            'FONTE-24V-2A', 'SIN-LED-24V', 'FIO-FLEX-1-5MM', 'DPS-20KA-275V', 'TERMINAL-OLHAL-4MM',
            'ABRACADEIRA-20CM', 'VALV-BORB-E6', 'TUBO-PVC-6', 'TE-PVC-6', 'BOLSA-FLG-6',
            'CURVA-PVC-90-6', 'BOLSA-FLG-2'
        ],
        'Descricao': [
            'CLP Autus Básico', 'CLP Autus Avançado', 'Painel 800x600', 'Painel 1000x600', 'Painel 1000x800',
            'Contator 12A', 'Relé Interface', 'Disjuntor Motor', 'Disjuntor 2A', 'Borne Terra',
            'Borne SAK 4mm', 'Canaleta 60x40', 'Trilho DIN', 'Vaso 30x72', 'Vaso 36x72',
            'Vaso 42x72', 'Vaso 48x72', 'Vaso 63x80', 'Válvula Borboleta 2"', 'Válvula Borboleta 3"',
            'Válvula Borboleta 4"', 'Zeolita 25kg', 'Tubo PVC 2"', 'Curva 90 PVC 2"', 'Tê PVC 2"',
            'Luva PVC 2"', 'Tubo PVC 3"', 'Curva 90 PVC 3"', 'Tê PVC 3"', 'Luva PVC 4"',
            'Tubo PVC 4"', 'Curva 90 PVC 4"', 'Tê PVC 4"', 'Bolsa Flange 4"', 'Parafuso Inox Kit',
            'Cola Aquatherm', 'Zeolita Suporte', 'Crepina 1"', 'IHM 7 Pol', 'IHM 10 Pol',
            'Fonte 24V', 'Sinaleiro LED', 'Fio Flexivel', 'DPS 20kA', 'Terminal Olhal',
            'Abraçadeira', 'Válvula Borboleta 6"', 'Tubo PVC 6"', 'Tê PVC 6"', 'Bolsa Flange 6"',
            'Curva 90 PVC 6"', 'Bolsa Flange 2"'
        ],
        'Grupo_Orcamento': [
            'CLP', 'CLP', 'Itens de Painel', 'Itens de Painel', 'Itens de Painel',
            'Itens de Painel', 'Itens de Painel', 'Itens de Painel', 'Itens de Painel', 'Itens de Painel',
            'Itens de Painel', 'Itens de Painel', 'Itens de Painel', 'Vasos', 'Vasos',
            'Vasos', 'Vasos', 'Vasos', 'Hidráulica', 'Hidráulica',
            'Hidráulica', 'Hidráulica', 'Hidráulica', 'Hidráulica', 'Hidráulica',
            'Hidráulica', 'Hidráulica', 'Hidráulica', 'Hidráulica', 'Hidráulica',
            'Hidráulica', 'Hidráulica', 'Hidráulica', 'Hidráulica', 'Hidráulica',
            'Hidráulica', 'Hidráulica', 'Hidráulica', 'Itens de Painel', 'Itens de Painel',
            'Itens de Painel', 'Itens de Painel', 'Itens de Painel', 'Itens de Painel', 'Itens de Painel',
            'Itens de Painel', 'Hidráulica', 'Hidráulica', 'Hidráulica', 'Hidráulica',
            'Hidráulica', 'Hidráulica'
        ],
        'Preco_Custo': [
            2500.0, 4500.0, 750.0, 950.0, 1100.0, 90.0, 40.0, 150.0, 35.0, 5.5,
            3.5, 45.0, 20.0, 6000.0, 7500.0, 8500.0, 9500.0, 15000.0, 700.0, 900.0,
            1200.0, 110.0, 90.0, 12.0, 15.0, 8.0, 150.0, 20.0, 24.0, 12.0,
            210.0, 28.0, 32.0, 42.0, 4.0, 25.0, 110.0, 35.0, 1800.0, 2600.0,
            180.0, 25.0, 150.0, 80.0, 30.0, 15.0, 1900.0, 350.0, 55.0, 60.0,
            45.0, 25.0
        ]
    },
    "MaoDeObra": {
        'ID_MaoDeObra': ['MDO-MONT-ELET', 'MDO-PROG-CLP', 'MDO-MONT-HIDR'],
        'Tipo_Servico': ['Montagem Painel Elétrico', 'Programação de CLP', 'Montagem Hidráulica'],
        'Grupo_Orcamento': ['Mão de Obra', 'Mão de Obra', 'Mão de Obra'],
        'Custo_Hora': [80.0, 150.0, 70.0]
    },
    "Config_Acionamentos": {
        'Num_Vasos': [1, 2, 3, 4],
        'ID_Material_CLP': ['CLP-AUT-01', 'CLP-AUT-01', 'CLP-AUT-02', 'CLP-AUT-02'],
        'ID_Material_Painel': ['PAINEL-8060', 'PAINEL-8060', 'PAINEL-10060', 'PAINEL-10080'],
        'ID_Material_IHM': ['IHM-AUT-7POL', 'IHM-AUT-7POL', 'IHM-AUT-10POL', 'IHM-AUT-10POL'],
        'ID_Kit_Painel_Eletrico': ['KIT-PAINEL-1V', 'KIT-PAINEL-2V', 'KIT-PAINEL-3V', 'KIT-PAINEL-4V'],
        'Horas_MDO_Mont_Elet': [16, 24, 32, 40],
        'Horas_MDO_Prog_CLP': [10, 16, 24, 30]
    },
    "Config_Vasos": {
        'Descricao_Vaso': ['30x72', '36x72', '42x72', '48x72', '63x80'],
        'ID_Material_Vaso': ['VASO-FIL-3072', 'VASO-FIL-3672', 'VASO-FIL-4272', 'VASO-FIL-4872', 'VASO-FIL-6380'],
        'Horas_MDO_Hidr_p_Vaso': [16, 18, 20, 22, 25]
    },
    "Config_Hidraulica": {
        'Descricao_Vaso': ['30x72', '36x72', '36x72', '42x72', '42x72', '48x72', '48x72', '63x80', '63x80'],
        'ID_Diametro_mm': [50, 50, 100, 100, 150, 100, 150, 100, 150],
        'ID_Kit_Hidraulico_p_Vaso': [
            'KIT-HID-3072-PV-50MM', 'KIT-HID-3672-PV-50MM', 'KIT-HID-3672-PV-100MM',
            'KIT-HID-4272-PV-100MM', 'KIT-HID-4272-PV-150MM', 'KIT-HID-4872-PV-100MM',
            'KIT-HID-4872-PV-150MM', 'KIT-HID-6380-PV-100MM', 'KIT-HID-6380-PV-150MM'
        ]
    },
    "Kits": {
        'ID_Kit': [], 'ID_Material': [], 'Quantidade': []
    }
}

# --- POPULAR KITS PADRÃO ---
def add_k(idk, idm, qtd):
    DEFAULT_DATA["Kits"]['ID_Kit'].append(idk)
    DEFAULT_DATA["Kits"]['ID_Material'].append(idm)
    DEFAULT_DATA["Kits"]['Quantidade'].append(qtd)

# Kits Painel
for m,q in [('CONT-MOT-12A',6),('RELE-INT-24V',6)]: add_k('KIT-PAINEL-1V', m, q)
for m,q in [('CONT-MOT-12A',12),('RELE-INT-24V',12)]: add_k('KIT-PAINEL-2V', m, q)
for m,q in [('CONT-MOT-12A',18),('RELE-INT-24V',18)]: add_k('KIT-PAINEL-3V', m, q)
for m,q in [('CONT-MOT-12A',24),('RELE-INT-24V',24),('DISJ-MOT-10A',24),('DISJ-COM-02A',1),
            ('BORNE-SAK-4',160),('BORNE-TERRA',40),('CANALETA-6040',5),('TRILHO-DIN',6),
            ('FONTE-24V-2A',1),('SIN-LED-24V',8),('FIO-FLEX-1-5MM',2),('DPS-20KA-275V',1),
            ('TERMINAL-OLHAL-4MM',4),('ABRACADEIRA-20CM',2)]: add_k('KIT-PAINEL-4V', m, q)

# Kits Hidráulicos
for k in ['KIT-HID-3672-PV-100MM', 'KIT-HID-4272-PV-100MM', 'KIT-HID-4872-PV-100MM', 'KIT-HID-6380-PV-100MM']:
    for m,q in [('MEDIA-ZEO-25',40),('VALV-BORB-E4',6),('ZEO-SUP-34',2),('CURVA-PVC-90-4',12),
                ('TE-PVC-4',5),('BOLSA-FLG-4',12),('PARAF-INOX-M10',48),('TUBO-PVC-4',2)]: add_k(k, m, q)
for k in ['KIT-HID-3072-PV-50MM', 'KIT-HID-3672-PV-50MM']:
    for m,q in [('MEDIA-ZEO-25',20),('VALV-BORB-E2',6),('CURVA-PVC-90-2',12),('TUBO-PVC-2',2)]: add_k(k, m, q)
for k in ['KIT-HID-4272-PV-150MM', 'KIT-HID-4872-PV-150MM', 'KIT-HID-6380-PV-150MM']:
    for m,q in [('MEDIA-ZEO-25',60),('VALV-BORB-E6',6),('CURVA-PVC-90-6',12),('TUBO-PVC-6',2)]: add_k(k, m, q)

# --- FUNÇÕES DE CARREGAMENTO ---
def load_data(force_reset=False):
    dataframes = {}
    for key, filename in FILES.items():
        if force_reset or not os.path.exists(filename):
            df = pd.DataFrame(DEFAULT_DATA.get(key, {}))
            df.to_csv(filename, index=False)
            dataframes[key] = df
        else:
            try:
                dataframes[key] = pd.read_csv(filename)
            except:
                df = pd.DataFrame(DEFAULT_DATA.get(key, {}))
                df.to_csv(filename, index=False)
                dataframes[key] = df
    return dataframes

def save_data(key, df):
    df.to_csv(FILES[key], index=False)
    st.toast(f"✅ Dados de {key} salvos com sucesso!", icon="💾")

# Reset Sidebar com Confirmação
with st.sidebar:
    st.header("⚙️ Opções")
    
    if 'confirma_reset' not in st.session_state:
        st.session_state.confirma_reset = False

    if st.button("⚠️ Restaurar Padrão"):
        st.session_state.confirma_reset = True

    if st.session_state.confirma_reset:
        st.warning("Tem certeza? Isso apagará todas as suas edições.")
        col_sim, col_nao = st.columns(2)
        with col_sim:
            if st.button("✅ Sim, Restaurar"):
                load_data(force_reset=True)
                st.success("Dados restaurados!")
                st.session_state.confirma_reset = False
                st.rerun()
        with col_nao:
            if st.button("❌ Cancelar"):
                st.session_state.confirma_reset = False
                st.rerun()

db = load_data()

# ==============================================================================
# 3. CÁLCULO (GERA A LISTA COMPLETA INICIAL)
# ==============================================================================
def calcular_itens_iniciais(num_vasos, tam_vaso, diametro, margens_dict):
    try:
        regra_painel = db["Config_Acionamentos"][db["Config_Acionamentos"]['Num_Vasos'] == num_vasos].iloc[0]
        regra_vaso = db["Config_Vasos"][db["Config_Vasos"]['Descricao_Vaso'] == tam_vaso].iloc[0]
        df_hidra = db["Config_Hidraulica"]
        filtro_hid = (df_hidra['Descricao_Vaso'] == tam_vaso) & (df_hidra['ID_Diametro_mm'] == diametro)
        
        if filtro_hid.sum() == 0: return None
        
        id_kit_hidra = df_hidra[filtro_hid].iloc[0]['ID_Kit_Hidraulico_p_Vaso']
        id_kit_painel = regra_painel['ID_Kit_Painel_Eletrico']

        itens = []
        # Soltos
        itens.append({'ID': regra_painel['ID_Material_CLP'], 'Qtd': 1, 'Tipo': 'Material'})
        itens.append({'ID': regra_painel['ID_Material_Painel'], 'Qtd': 1, 'Tipo': 'Material'})
        itens.append({'ID': regra_painel['ID_Material_IHM'], 'Qtd': 1, 'Tipo': 'Material'})
        itens.append({'ID': regra_vaso['ID_Material_Vaso'], 'Qtd': num_vasos, 'Tipo': 'Material'})
        
        # Kits
        df_kits = db["Kits"]
        for k, f in [(id_kit_painel, 1), (id_kit_hidra, num_vasos)]:
            k_itens = df_kits[df_kits['ID_Kit'] == k]
            if k_itens.empty: st.warning(f"Kit {k} vazio.")
            for _, r in k_itens.iterrows():
                itens.append({'ID': r['ID_Material'], 'Qtd': r['Quantidade'] * f, 'Tipo': 'Material'})

        # MDO
        itens.append({'ID': 'MDO-MONT-ELET', 'Qtd': regra_painel['Horas_MDO_Mont_Elet'], 'Tipo': 'MDO'})
        itens.append({'ID': 'MDO-PROG-CLP', 'Qtd': regra_painel['Horas_MDO_Prog_CLP'], 'Tipo': 'MDO'})
        itens.append({'ID': 'MDO-MONT-HIDR', 'Qtd': regra_vaso['Horas_MDO_Hidr_p_Vaso'] * num_vasos, 'Tipo': 'MDO'})

        res = []
        df_mat, df_mdo = db["Materiais"], db["MaoDeObra"]

        for item in itens:
            if item['Tipo'] == 'Material':
                d = df_mat[df_mat['ID_Material'] == item['ID']]
                if d.empty: continue
                desc, grp, cust = d.iloc[0]['Descricao'], d.iloc[0]['Grupo_Orcamento'], float(d.iloc[0]['Preco_Custo'])
                mrg = margens_dict.get(grp, 0.5)
            else:
                d = df_mdo[df_mdo['ID_MaoDeObra'] == item['ID']]
                desc, grp, cust = d.iloc[0]['Tipo_Servico'], "Mão de Obra", float(d.iloc[0]['Custo_Hora'])
                
                # Margem Específica para cada MDO
                if item['ID'] == 'MDO-MONT-ELET': mrg = margens_dict.get("MDO_Elet", 0.5)
                elif item['ID'] == 'MDO-PROG-CLP': mrg = margens_dict.get("MDO_Prog", 0.5)
                elif item['ID'] == 'MDO-MONT-HIDR': mrg = margens_dict.get("MDO_Hidr", 0.5)
                else: mrg = 0.5

            unit_venda = cust * (1 + mrg)
            tot_cust = cust * item['Qtd']
            tot_vend = unit_venda * item['Qtd']
            
            res.append({
                'Incluir': True,
                'Descrição': desc, 
                'Grupo': grp, 
                'Qtd': item['Qtd'], 
                'Custo Unit': cust,
                'Venda Unit': unit_venda,
                'Total Venda': tot_vend,
                'Total Custo': tot_cust
            })

        return pd.DataFrame(res)
    except:
        return None

# ==============================================================================
# 4. INTERFACE
# ==============================================================================

tab_dash, tab_kits, tab_db = st.tabs(["📊 Dashboard", "🛠️ Construtor de Kits", "🗃️ Banco de Dados"])

with tab_dash:
    st.title("Simulador de Orçamento")
    c1, c2, c3 = st.columns(3)
    with c1: sel_vasos = st.selectbox("Nº Vasos", [1,2,3,4], index=3)
    with c2: sel_tamanho = st.selectbox("Tamanho", db["Config_Vasos"]['Descricao_Vaso'].unique(), index=3)
    with c3: sel_diametro = st.selectbox("Diâmetro", db["Config_Hidraulica"]['ID_Diametro_mm'].unique(), index=1)
    
    st.divider()
    st.subheader("Configuração de Margens (%)")
    
    # Linha 1: Materiais (INPUT NUMÉRICO)
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    m_clp = col_m1.number_input("CLP", min_value=0.0, max_value=500.0, value=50.0, step=1.0) / 100
    m_painel = col_m2.number_input("Painel (Peças)", min_value=0.0, max_value=500.0, value=50.0, step=1.0) / 100
    m_hidra = col_m3.number_input("Hidráulica", min_value=0.0, max_value=500.0, value=50.0, step=1.0) / 100
    m_vasos = col_m4.number_input("Vasos", min_value=0.0, max_value=500.0, value=50.0, step=1.0) / 100
    
    # Linha 2: Mão de Obra (INPUT NUMÉRICO)
    col_md1, col_md2, col_md3 = st.columns(3)
    m_mdo_elet = col_md1.number_input("MDO Elétrica", min_value=0.0, max_value=500.0, value=50.0, step=1.0) / 100
    m_mdo_prog = col_md2.number_input("MDO Programação", min_value=0.0, max_value=500.0, value=50.0, step=1.0) / 100
    m_mdo_hidr = col_md3.number_input("MDO Hidráulica", min_value=0.0, max_value=500.0, value=50.0, step=1.0) / 100

    MARGENS = {
        "CLP": m_clp, "Itens de Painel": m_painel, "Hidráulica": m_hidra, "Vasos": m_vasos,
        "MDO_Elet": m_mdo_elet, "MDO_Prog": m_mdo_prog, "MDO_Hidr": m_mdo_hidr
    }
    
    df_inicial = calcular_itens_iniciais(sel_vasos, sel_tamanho, sel_diametro, MARGENS)
    
    if df_inicial is None:
        st.error("Configuração inválida (Kit Hidráulico não encontrado).")
    else:
        st.divider()
        st.markdown("### Selecione os itens para o Orçamento:")
        
        df_editado = st.data_editor(
            df_inicial,
            column_config={
                "Incluir": st.column_config.CheckboxColumn("Incluir?", default=True),
                "Custo Unit": st.column_config.NumberColumn(format="R$ %.2f"),
                "Venda Unit": st.column_config.NumberColumn(format="R$ %.2f"),
                "Total Venda": st.column_config.NumberColumn(format="R$ %.2f"),
                "Total Custo": None 
            },
            disabled=["Descrição", "Grupo", "Qtd", "Custo Unit", "Venda Unit", "Total Venda"],
            hide_index=True,
            use_container_width=True,
            height=400
        )

        df_final = df_editado[df_editado['Incluir'] == True].copy()
        
        venda_final = df_final['Total Venda'].sum()
        custo_final = df_final['Total Custo'].sum()
        lucro = venda_final - custo_final
        lucro_pct = (lucro/custo_final*100) if custo_final > 0 else 0
        
        st.divider()
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Valor Final", f"R$ {venda_final:,.2f}")
        k2.metric("Custo Estimado", f"R$ {custo_final:,.2f}")
        k3.metric("Lucro R$", f"R$ {lucro:,.2f}")
        k4.metric("Margem Real %", f"{lucro_pct:.1f}%")
        
        if st.button("📄 BAIXAR PDF (Itens Selecionados)", type="primary"):
            class PDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 14); self.cell(0, 10, 'Orcamento Comercial', 0, 1, 'C'); self.ln(5)
            pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
            pdf.cell(0, 6, f"Data: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
            pdf.cell(0, 6, f"Config: {sel_vasos} Vasos | {sel_tamanho}", 0, 1); pdf.ln(5)
            
            pdf.set_fill_color(220, 220, 220); pdf.set_font("Arial", 'B', 9)
            pdf.cell(80, 8, "Item", 1, 0, 'L', 1); pdf.cell(15, 8, "Qtd", 1, 0, 'C', 1)
            pdf.cell(30, 8, "Unit", 1, 0, 'R', 1); pdf.cell(35, 8, "Total", 1, 1, 'R', 1)
            
            pdf.set_font("Arial", size=9)
            for _, r in df_final.iterrows():
                pdf.cell(80, 7, str(r['Descrição'])[0:40], 1); pdf.cell(15, 7, str(r['Qtd']), 1, 0, 'C')
                pdf.cell(30, 7, f"{r['Venda Unit']:,.2f}", 1, 0, 'R'); pdf.cell(35, 7, f"{r['Total Venda']:,.2f}", 1, 1, 'R')
            
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, f"TOTAL: R$ {venda_final:,.2f}", 0, 1, 'R')
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf"); pdf.output(temp.name)
            with open(temp.name, "rb") as f: st.download_button("📥 Download PDF", f, "orcamento_final.pdf")

# --- ABA 2 E 3 (IGUAIS) ---
with tab_kits:
    st.header("🛠️ Configuração de Kits")
    kits_existentes = sorted(db["Kits"]['ID_Kit'].unique())
    col_k1, col_k2 = st.columns([2, 1])
    with col_k1: kit_selecionado = st.selectbox("Selecione Kit:", kits_existentes)
    with col_k2:
        novo_kit = st.text_input("Novo Kit (ID):")
        if st.button("Criar") and novo_kit:
            if novo_kit not in kits_existentes:
                db["Kits"] = pd.concat([db["Kits"], pd.DataFrame({'ID_Kit':[novo_kit],'ID_Material':[''],'Quantidade':[0]})], ignore_index=True)
                save_data("Kits", db["Kits"]); st.rerun()
    if novo_kit and novo_kit in kits_existentes: kit_selecionado = novo_kit

    df_k = db["Kits"][db["Kits"]['ID_Kit'] == kit_selecionado].copy()
    df_m = db["Materiais"][['ID_Material', 'Descricao']]
    df_d = pd.merge(df_k, df_m, on='ID_Material', how='left')
    
    c_lst, c_add = st.columns([2, 1])
    with c_lst:
        st.subheader("Itens Atuais")
        df_ed = st.data_editor(df_d[['ID_Material', 'Descricao', 'Quantidade']], key="edit_kit", num_rows="dynamic")
        if st.button("💾 Salvar Kit"):
            db["Kits"] = db["Kits"][db["Kits"]['ID_Kit'] != kit_selecionado]
            df_s = df_ed.copy(); df_s['ID_Kit'] = kit_selecionado
            db["Kits"] = pd.concat([db["Kits"], df_s[['ID_Kit', 'ID_Material', 'Quantidade']]], ignore_index=True)
            db["Kits"] = db["Kits"][db["Kits"]['ID_Material'] != '']; save_data("Kits", db["Kits"]); st.rerun()
    with c_add:
        st.subheader("Adicionar")
        opt = df_m.apply(lambda x: f"{x['Descricao']} | {x['ID_Material']}", axis=1)
        sel = st.selectbox("Material:", opt); qtd = st.number_input("Qtd:", 1.0)
        if st.button("➕ Add"):
            db["Kits"] = pd.concat([db["Kits"], pd.DataFrame({'ID_Kit':[kit_selecionado],'ID_Material':[sel.split(" | ")[-1]],'Quantidade':[qtd]})], ignore_index=True)
            save_data("Kits", db["Kits"]); st.rerun()

with tab_db:
    st.header("🗃️ Dados Brutos")
    tab = st.selectbox("Tabela", list(FILES.keys()))
    de = st.data_editor(db[tab], num_rows="dynamic", use_container_width=True)
    if st.button("Salvar DB"): save_data(tab, de); st.rerun()
