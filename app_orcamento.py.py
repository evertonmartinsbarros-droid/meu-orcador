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

# CSS para visual estilo Power BI
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
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. GERENCIAMENTO DE DADOS (CARREGAR E SALVAR)
# ==============================================================================
FILES = {
    "Materiais": "db_materiais.csv",
    "MaoDeObra": "db_mdo.csv",
    "Kits": "db_kits.csv",
    "Config_Acionamentos": "db_conf_acion.csv",
    "Config_Vasos": "db_conf_vasos.csv",
    "Config_Hidraulica": "db_conf_hidra.csv"
}

# DADOS PADRÃO (Caso não existam arquivos)
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

# Kit 4V
for m,q in [('CONT-MOT-12A',24),('RELE-INT-24V',24),('DISJ-MOT-10A',24),('DISJ-COM-02A',1),
            ('BORNE-SAK-4',160),('BORNE-TERRA',40),('CANALETA-6040',5),('TRILHO-DIN',6),
            ('FONTE-24V-2A',1),('SIN-LED-24V',8),('FIO-FLEX-1-5MM',2),('DPS-20KA-275V',1),
            ('TERMINAL-OLHAL-4MM',4),('ABRACADEIRA-20CM',2)]: add_k('KIT-PAINEL-4V', m, q)

# Outros Kits
for m,q in [('CONT-MOT-12A',6),('RELE-INT-24V',6)]: add_k('KIT-PAINEL-1V', m, q)
for m,q in [('CONT-MOT-12A',12),('RELE-INT-24V',12)]: add_k('KIT-PAINEL-2V', m, q)
for m,q in [('CONT-MOT-12A',18),('RELE-INT-24V',18)]: add_k('KIT-PAINEL-3V', m, q)

for k in ['KIT-HID-3672-PV-100MM', 'KIT-HID-4272-PV-100MM', 'KIT-HID-4872-PV-100MM', 'KIT-HID-6380-PV-100MM']:
    for m,q in [('MEDIA-ZEO-25',40),('VALV-BORB-E4',6),('ZEO-SUP-34',2),('CURVA-PVC-90-4',12),
                ('TE-PVC-4',5),('BOLSA-FLG-4',12),('PARAF-INOX-M10',48),('TUBO-PVC-4',2)]: add_k(k, m, q)

# Funções de IO
def load_data():
    dataframes = {}
    for key, filename in FILES.items():
        if os.path.exists(filename):
            dataframes[key] = pd.read_csv(filename)
        else:
            df = pd.DataFrame(DEFAULT_DATA.get(key, {}))
            df.to_csv(filename, index=False)
            dataframes[key] = df
    return dataframes

def save_data(key, df):
    df.to_csv(FILES[key], index=False)
    st.toast(f"✅ Dados de {key} salvos com sucesso!", icon="💾")

# Carrega DB
db = load_data()

# ==============================================================================
# 3. MOTOR DE CÁLCULO (TEMPO REAL)
# ==============================================================================
def calcular_orcamento(num_vasos, tam_vaso, diametro, margens_dict):
    df_mat = db["Materiais"]
    df_mdo = db["MaoDeObra"]
    df_kits = db["Kits"]
    df_conf_acion = db["Config_Acionamentos"]
    df_conf_vasos = db["Config_Vasos"]
    df_conf_hidra = db["Config_Hidraulica"]

    try:
        regra_painel = df_conf_acion[df_conf_acion['Num_Vasos'] == num_vasos].iloc[0]
        regra_vaso = df_conf_vasos[df_conf_vasos['Descricao_Vaso'] == tam_vaso].iloc[0]
        filtro_hid = (df_conf_hidra['Descricao_Vaso'] == tam_vaso) & (df_conf_hidra['ID_Diametro_mm'] == diametro)
        
        if filtro_hid.sum() == 0: return None, "Combinação de Vaso e Diâmetro não cadastrada."
        id_kit_hidra = df_conf_hidra[filtro_hid].iloc[0]['ID_Kit_Hidraulico_p_Vaso']
        id_kit_painel = regra_painel['ID_Kit_Painel_Eletrico']
    except:
        return None, "Erro ao buscar configurações."

    itens = []
    # Soltos
    itens.append({'ID': regra_painel['ID_Material_CLP'], 'Qtd': 1, 'Tipo': 'Material'})
    itens.append({'ID': regra_painel['ID_Material_Painel'], 'Qtd': 1, 'Tipo': 'Material'})
    itens.append({'ID': regra_painel['ID_Material_IHM'], 'Qtd': 1, 'Tipo': 'Material'})
    itens.append({'ID': regra_vaso['ID_Material_Vaso'], 'Qtd': num_vasos, 'Tipo': 'Material'})
    # Kits
    for k, f in [(id_kit_painel, 1), (id_kit_hidra, num_vasos)]:
        for _, r in df_kits[df_kits['ID_Kit'] == k].iterrows():
            itens.append({'ID': r['ID_Material'], 'Qtd': r['Quantidade'] * f, 'Tipo': 'Material'})
    # MDO
    itens.append({'ID': 'MDO-MONT-ELET', 'Qtd': regra_painel['Horas_MDO_Mont_Elet'], 'Tipo': 'MDO'})
    itens.append({'ID': 'MDO-PROG-CLP', 'Qtd': regra_painel['Horas_MDO_Prog_CLP'], 'Tipo': 'MDO'})
    itens.append({'ID': 'MDO-MONT-HIDR', 'Qtd': regra_vaso['Horas_MDO_Hidr_p_Vaso'] * num_vasos, 'Tipo': 'MDO'})

    res, custo_tot, venda_tot = [], 0, 0
    for item in itens:
        if item['Tipo'] == 'Material':
            d = df_mat[df_mat['ID_Material'] == item['ID']]
            if d.empty: continue
            desc, grp, cust = d.iloc[0]['Descricao'], d.iloc[0]['Grupo_Orcamento'], float(d.iloc[0]['Preco_Custo'])
        else:
            d = df_mdo[df_mdo['ID_MaoDeObra'] == item['ID']]
            desc, grp, cust = d.iloc[0]['Tipo_Servico'], "Mão de Obra", float(d.iloc[0]['Custo_Hora'])

        mrg = margens_dict.get(grp, 0.5)
        tot_cust = cust * item['Qtd']
        tot_vend = tot_cust * (1 + mrg)
        
        res.append({'Descrição': desc, 'Grupo': grp, 'Qtd': item['Qtd'], 'Custo Unit': cust, 'Preço Venda': tot_vend})
        custo_tot += tot_cust
        venda_tot += tot_vend

    return pd.DataFrame(res), custo_tot, venda_tot

# ==============================================================================
# 4. INTERFACE PRINCIPAL (ABAS)
# ==============================================================================

tab_dash, tab_config = st.tabs(["📊 Dashboard de Orçamento", "⚙️ Configuração de Itens"])

# --- ABA 1: DASHBOARD (VISUAL POWER BI) ---
with tab_dash:
    st.title("Simulador de Orçamento")
    
    # 1. Filtros (COM PROTEÇÃO DE ÍNDICE)
    c1, c2, c3 = st.columns(3)
    
    with c1: 
        opcoes_vasos = [1, 2, 3, 4]
        # Seleciona o ultimo (3) se existir, senão 0
        idx_vasos = 3 if len(opcoes_vasos) > 3 else 0
        sel_vasos = st.selectbox("Nº de Vasos", opcoes_vasos, index=idx_vasos)

    with c2: 
        opcoes_tamanho = db["Config_Vasos"]['Descricao_Vaso'].unique()
        idx_tamanho = 3 if len(opcoes_tamanho) > 3 else 0
        sel_tamanho = st.selectbox("Tamanho do Vaso", opcoes_tamanho, index=idx_tamanho)

    with c3: 
        opcoes_diametro = db["Config_Hidraulica"]['ID_Diametro_mm'].unique()
        # Seleciona o segundo (1) se existir, senão 0
        idx_diametro = 1 if len(opcoes_diametro) > 1 else 0
        sel_diametro = st.selectbox("Diâmetro Tubulação", opcoes_diametro, index=idx_diametro)
    
    st.divider()
    
    # 2. Sliders Margem
    st.caption("Definição de Margens (%)")
    m1, m2, m3, m4, m5 = st.columns(5)
    margem_clp = m1.slider("CLP", 0, 100, 50) / 100
    margem_hidra = m2.slider("Hidráulica", 0, 100, 50) / 100
    margem_painel = m3.slider("Painel", 0, 100, 50) / 100
    margem_mdo = m4.slider("MDO", 0, 100, 50) / 100
    margem_vasos = m5.slider("Vasos", 0, 100, 50) / 100
    
    MARGENS = {"CLP": margem_clp, "Hidráulica": margem_hidra, "Itens de Painel": margem_painel, "Mão de Obra": margem_mdo, "Vasos": margem_vasos}
    
    # 3. Cálculo e KPIs
    df_res, custo_total, venda_total = calcular_orcamento(sel_vasos, sel_tamanho, sel_diametro, MARGENS)
    
    if df_res is None:
        st.error("❌ Configuração inválida.")
    else:
        margem_reais = venda_total - custo_total
        margem_pct = (margem_reais / custo_total * 100) if custo_total > 0 else 0
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Preço Venda", f"R$ {venda_total:,.2f}")
        k2.metric("Custo Total", f"R$ {custo_total:,.2f}")
        k3.metric("Margem R$", f"R$ {margem_reais:,.2f}")
        k4.metric("Margem %", f"{margem_pct:.1f}%")
        
        st.divider()
        
        # 4. Tabela
        st.subheader("Detalhamento")
        df_show = df_res.copy()
        df_show['Custo Unit'] = df_show['Custo Unit'].map('R$ {:,.2f}'.format)
        df_show['Preço Venda'] = df_show['Preço Venda'].map('R$ {:,.2f}'.format)
        st.dataframe(df_show, use_container_width=True, height=400)
        
        # 5. BOTÃO GERAR PDF (NOVO!)
        st.write("")
        col_btn_L, col_btn_R = st.columns([4, 1])
        with col_btn_R:
            if st.button("📄 BAIXAR ORÇAMENTO PDF", type="primary"):
                class PDF(FPDF):
                    def header(self):
                        self.set_font('Arial', 'B', 14)
                        self.cell(0, 10, 'Orcamento Comercial', 0, 1, 'C')
                        self.ln(5)
                
                pdf = PDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.cell(0, 6, f"Data: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
                pdf.cell(0, 6, f"Projeto: {sel_vasos} Vasos | {sel_tamanho} | {sel_diametro}mm", 0, 1)
                pdf.ln(5)
                
                # Cabeçalho Tabela PDF
                pdf.set_fill_color(220, 220, 220)
                pdf.set_font("Arial", 'B', 9)
                pdf.cell(100, 8, "Item", 1, 0, 'L', 1)
                pdf.cell(20, 8, "Qtd", 1, 0, 'C', 1)
                pdf.cell(35, 8, "Total (R$)", 1, 1, 'R', 1)
                
                # Itens
                pdf.set_font("Arial", size=9)
                for _, row in df_res.iterrows():
                    pdf.cell(100, 7, str(row['Descrição'])[0:55], 1)
                    pdf.cell(20, 7, str(row['Qtd']), 1, 0, 'C')
                    pdf.cell(35, 7, f"{row['Preço Venda']:,.2f}", 1, 1, 'R')
                
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, f"TOTAL: R$ {venda_total:,.2f}", 0, 1, 'R')
                
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                pdf.output(temp.name)
                
                with open(temp.name, "rb") as f:
                    st.download_button("📥 Clique para Salvar", f, "orcamento.pdf", mime="application/pdf")

# --- ABA 2: CONFIGURAÇÃO (EDITOR DE DADOS) ---
with tab_config:
    st.header("🛠️ Configuração de Itens e Preços")
    st.info("Selecione a tabela abaixo para editar. As alterações são salvas automaticamente ao clicar no botão.")
    
    tabela_selecionada = st.selectbox("Selecione a Tabela:", list(FILES.keys()))
    
    # Editor
    df_editavel = st.data_editor(
        db[tabela_selecionada],
        num_rows="dynamic", # Permite adicionar linhas
        use_container_width=True,
        height=600
    )
    
    if st.button("💾 SALVAR ALTERAÇÕES NA TABELA"):
        save_data(tabela_selecionada, df_editavel)
        st.rerun() # Recarrega a página para atualizar o dashboard
