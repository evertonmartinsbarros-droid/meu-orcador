import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import tempfile
import os

# ==============================================================================
# 1. DADOS PADRÃO CORRIGIDOS (IDÊNTICOS AO POWER BI FINAL)
# ==============================================================================

st.set_page_config(page_title="Orçamentador Power BI", page_icon="📊", layout="wide")

FILES = {
    "Materiais": "db_materiais.csv",
    "MaoDeObra": "db_mdo.csv",
    "Kits": "db_kits.csv",
    "Config_Acionamentos": "db_conf_acion.csv",
    "Config_Vasos": "db_conf_vasos.csv",
    "Config_Hidraulica": "db_conf_hidra.csv"
}

# DADOS LIMPOS E COMPLETOS (Incluindo Kit 4V e novos itens)
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

# POPULAR OS KITS (Incluindo o 4V que faltava)
def add_k(idk, idm, qtd):
    DEFAULT_DATA["Kits"]['ID_Kit'].append(idk)
    DEFAULT_DATA["Kits"]['ID_Material'].append(idm)
    DEFAULT_DATA["Kits"]['Quantidade'].append(qtd)

# KIT 4V COMPLETO
kit4 = 'KIT-PAINEL-4V'
for m,q in [('CONT-MOT-12A',24),('RELE-INT-24V',24),('DISJ-MOT-10A',24),('DISJ-COM-02A',1),
            ('BORNE-SAK-4',160),('BORNE-TERRA',40),('CANALETA-6040',5),('TRILHO-DIN',6),
            ('FONTE-24V-2A',1),('SIN-LED-24V',8),('FIO-FLEX-1-5MM',2),('DPS-20KA-275V',1),
            ('TERMINAL-OLHAL-4MM',4),('ABRACADEIRA-20CM',2)]:
    add_k(kit4, m, q)

# KITS 1V, 2V, 3V (Resumidos para exemplo, adicione completos se quiser)
add_k('KIT-PAINEL-1V', 'CONT-MOT-12A', 6); add_k('KIT-PAINEL-1V', 'RELE-INT-24V', 6)
add_k('KIT-PAINEL-2V', 'CONT-MOT-12A', 12); add_k('KIT-PAINEL-2V', 'RELE-INT-24V', 12)
add_k('KIT-PAINEL-3V', 'CONT-MOT-12A', 18); add_k('KIT-PAINEL-3V', 'RELE-INT-24V', 18)

# KITS HIDRAULICOS (Exemplo do 48x72 100mm)
kith = 'KIT-HID-4872-PV-100MM'
for m,q in [('MEDIA-ZEO-25',40),('VALV-BORB-E4',6),('ZEO-SUP-34',2),('CREPINA-FIL-1',2),
            ('CURVA-PVC-90-4',12),('TE-PVC-4',5),('BOLSA-FLG-4',12),('PARAF-INOX-M10',48),
            ('COLA-AQUA-Tubo',1),('TUBO-PVC-4',2)]:
    add_k(kith, m, q)


# --- CARREGAMENTO DE DADOS ---
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
    st.success(f"Salvo em {FILES[key]}")

db = load_data()

# ==============================================================================
# 2. CÁLCULO COM MULTI-MARGENS (IGUAL POWER BI)
# ==============================================================================

def calcular_orcamento_v3(num_vasos, tam_vaso, diametro, margens_dict):
    df_mat = db["Materiais"]
    df_mdo = db["MaoDeObra"]
    df_kits = db["Kits"]
    df_conf_acion = db["Config_Acionamentos"]
    df_conf_vasos = db["Config_Vasos"]
    df_conf_hidra = db["Config_Hidraulica"]

    # 1. Buscar Regras
    try:
        regra_painel = df_conf_acion[df_conf_acion['Num_Vasos'] == num_vasos].iloc[0]
        regra_vaso = df_conf_vasos[df_conf_vasos['Descricao_Vaso'] == tam_vaso].iloc[0]
        
        filtro_hid = (df_conf_hidra['Descricao_Vaso'] == tam_vaso) & (df_conf_hidra['ID_Diametro_mm'] == diametro)
        if filtro_hid.sum() == 0: return None, "❌ Kit Hidráulico não encontrado para essa medida."
        
        id_kit_hidra = df_conf_hidra[filtro_hid].iloc[0]['ID_Kit_Hidraulico_p_Vaso']
        id_kit_painel = regra_painel['ID_Kit_Painel_Eletrico']
    except Exception as e:
        return None, f"Erro de Configuração: {str(e)}"

    itens = []
    # Itens Soltos
    itens.append({'ID': regra_painel['ID_Material_CLP'], 'Qtd': 1, 'Tipo': 'Material'})
    itens.append({'ID': regra_painel['ID_Material_Painel'], 'Qtd': 1, 'Tipo': 'Material'})
    itens.append({'ID': regra_painel['ID_Material_IHM'], 'Qtd': 1, 'Tipo': 'Material'})
    itens.append({'ID': regra_vaso['ID_Material_Vaso'], 'Qtd': num_vasos, 'Tipo': 'Material'})

    # Kits
    k_painel = df_kits[df_kits['ID_Kit'] == id_kit_painel]
    for _, r in k_painel.iterrows(): itens.append({'ID': r['ID_Material'], 'Qtd': r['Quantidade'], 'Tipo': 'Material'})
    
    k_hidra = df_kits[df_kits['ID_Kit'] == id_kit_hidra]
    for _, r in k_hidra.iterrows(): itens.append({'ID': r['ID_Material'], 'Qtd': r['Quantidade'] * num_vasos, 'Tipo': 'Material'})

    # Mão de Obra
    itens.append({'ID': 'MDO-MONT-ELET', 'Qtd': regra_painel['Horas_MDO_Mont_Elet'], 'Tipo': 'MDO'})
    itens.append({'ID': 'MDO-PROG-CLP', 'Qtd': regra_painel['Horas_MDO_Prog_CLP'], 'Tipo': 'MDO'})
    itens.append({'ID': 'MDO-MONT-HIDR', 'Qtd': regra_vaso['Horas_MDO_Hidr_p_Vaso'] * num_vasos, 'Tipo': 'MDO'})

    resultado = []
    total_geral = 0

    for item in itens:
        if item['Tipo'] == 'Material':
            dado = df_mat[df_mat['ID_Material'] == item['ID']]
            if dado.empty: continue
            desc = dado.iloc[0]['Descricao']
            grupo = dado.iloc[0]['Grupo_Orcamento']
            custo = float(dado.iloc[0]['Preco_Custo'])
        else:
            dado = df_mdo[df_mdo['ID_MaoDeObra'] == item['ID']]
            desc = dado.iloc[0]['Tipo_Servico']
            grupo = "Mão de Obra"
            custo = float(dado.iloc[0]['Custo_Hora'])

        # APLICAR MARGEM ESPECÍFICA DO GRUPO (IGUAL POWER BI)
        margem_aplicada = margens_dict.get(grupo, 0.5) # Padrão 50% se não achar

        preco_venda = custo * (1 + margem_aplicada) * item['Qtd']
        
        resultado.append({
            'ID': item['ID'], 'Descrição': desc, 'Grupo': grupo, 'Qtd': item['Qtd'],
            'Custo Unit': custo, 'Margem': f"{margem_aplicada*100:.0f}%", 'Total Venda': preco_venda
        })
        total_geral += preco_venda

    return pd.DataFrame(resultado), total_geral

# ==============================================================================
# 3. INTERFACE
# ==============================================================================

tab1, tab2 = st.tabs(["📊 Orçamento Power BI", "🛠️ Editor de Dados"])

with tab1:
    st.header("Simulador de Orçamento")
    
    # --- MENU DE CONFIGURAÇÃO ---
    c1, c2, c3 = st.columns(3)
    with c1: vaso_sel = st.selectbox("Nº Vasos", [1,2,3,4], index=3)
    with c2: tam_sel = st.selectbox("Tamanho", db["Config_Vasos"]['Descricao_Vaso'].unique(), index=3)
    with c3: diam_sel = st.selectbox("Diâmetro", [50, 100, 150], index=1)

    st.divider()
    
    # --- SLIDERS DE MARGEM (O PEDIDO PRINCIPAL) ---
    st.subheader("Margens de Lucro por Categoria")
    cm1, cm2, cm3, cm4, cm5 = st.columns(5)
    
    # Padrões do Power BI (50%)
    m_clp = cm1.slider("CLP %", 0, 200, 50) / 100
    m_painel = cm2.slider("Painel %", 0, 200, 50) / 100
    m_hidra = cm3.slider("Hidráulica %", 0, 200, 50) / 100
    m_vasos = cm4.slider("Vasos %", 0, 200, 50) / 100
    m_mdo = cm5.slider("Mão de Obra %", 0, 200, 50) / 100

    # Dicionário para passar à função
    MARGENS = {
        "CLP": m_clp,
        "Itens de Painel": m_painel,
        "Hidráulica": m_hidra,
        "Vasos": m_vasos,
        "Mão de Obra": m_mdo
    }

    if st.button("CALCULAR ORÇAMENTO", type="primary"):
        df_res, total = calcular_orcamento_v3(vaso_sel, tam_sel, diam_sel, MARGENS)
        
        if isinstance(total, str):
            st.error(total)
        else:
            st.success(f"### VALOR TOTAL: R$ {total:,.2f}")
            
            # Mostra Tabela Bonita
            st.dataframe(df_res[['Descrição', 'Grupo', 'Qtd', 'Margem', 'Total Venda']], use_container_width=True)

            # Gerar PDF
            class PDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 14)
                    self.cell(0, 10, 'Orcamento Comercial Detalhado', 0, 1, 'C')
                    self.ln(5)
            
            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 6, f"Data: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
            pdf.cell(0, 6, f"Config: {vaso_sel} Vasos | {tam_sel} | {diam_sel}mm", 0, 1)
            pdf.ln(5)
            
            # Tabela PDF
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(90, 8, "Descricao", 1, 0, 'L', 1)
            pdf.cell(30, 8, "Grupo", 1, 0, 'C', 1)
            pdf.cell(20, 8, "Qtd", 1, 0, 'C', 1)
            pdf.cell(40, 8, "Total (R$)", 1, 1, 'R', 1)
            
            for _, r in df_res.iterrows():
                pdf.cell(90, 7, str(r['Descrição'])[0:45], 1)
                pdf.cell(30, 7, str(r['Grupo'])[0:15], 1, 0, 'C')
                pdf.cell(20, 7, str(r['Qtd']), 1, 0, 'C')
                pdf.cell(40, 7, f"{r['Total Venda']:,.2f}", 1, 1, 'R')
                
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, f"TOTAL GERAL: R$ {total:,.2f}", 0, 1, 'R')
            
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf.output(temp.name)
            with open(temp.name, "rb") as f:
                st.download_button("📥 Baixar PDF", f, "orcamento.pdf", mime="application/pdf")

with tab2:
    st.info("Edite os dados base aqui.")
    op = st.selectbox("Tabela", list(FILES.keys()))
    df_ed = st.data_editor(db[op], num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Alterações"):
        save_data(op, df_ed)
        st.rerun()
