import streamlit as st
import pandas as pd
import os

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================
st.set_page_config(page_title="Simulador de Orçamento", page_icon="📊", layout="wide")

# CSS para deixar os cartões (KPIs) mais bonitos e parecidos com o Power BI
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 24px;
        color: #00CC96; /* Verde parecida com o Power BI */
    }
    [data-testid="stMetricLabel"] {
        font-weight: bold;
        color: #888888;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DADOS (BASE COMPLETA E CORRIGIDA)
# ==============================================================================
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

# POPULAR OS KITS (Incluindo o 4V)
def add_k(idk, idm, qtd):
    DEFAULT_DATA["Kits"]['ID_Kit'].append(idk)
    DEFAULT_DATA["Kits"]['ID_Material'].append(idm)
    DEFAULT_DATA["Kits"]['Quantidade'].append(qtd)

# KIT 4V
for m,q in [('CONT-MOT-12A',24),('RELE-INT-24V',24),('DISJ-MOT-10A',24),('DISJ-COM-02A',1),
            ('BORNE-SAK-4',160),('BORNE-TERRA',40),('CANALETA-6040',5),('TRILHO-DIN',6),
            ('FONTE-24V-2A',1),('SIN-LED-24V',8),('FIO-FLEX-1-5MM',2),('DPS-20KA-275V',1),
            ('TERMINAL-OLHAL-4MM',4),('ABRACADEIRA-20CM',2)]:
    add_k('KIT-PAINEL-4V', m, q)

# KITS 1V, 2V, 3V (Simples para funcionamento)
for m,q in [('CONT-MOT-12A',6),('RELE-INT-24V',6)]: add_k('KIT-PAINEL-1V', m, q)
for m,q in [('CONT-MOT-12A',12),('RELE-INT-24V',12)]: add_k('KIT-PAINEL-2V', m, q)
for m,q in [('CONT-MOT-12A',18),('RELE-INT-24V',18)]: add_k('KIT-PAINEL-3V', m, q)

# KITS HIDRAULICOS (Todos os 100mm)
for k in ['KIT-HID-3672-PV-100MM', 'KIT-HID-4272-PV-100MM', 'KIT-HID-4872-PV-100MM', 'KIT-HID-6380-PV-100MM']:
    for m,q in [('MEDIA-ZEO-25',40),('VALV-BORB-E4',6),('ZEO-SUP-34',2),('CURVA-PVC-90-4',12),
                ('TE-PVC-4',5),('BOLSA-FLG-4',12),('PARAF-INOX-M10',48),('TUBO-PVC-4',2)]:
        add_k(k, m, q)
# KITS HIDRAULICOS (Todos os 50mm)
for k in ['KIT-HID-3072-PV-50MM', 'KIT-HID-3672-PV-50MM']:
    for m,q in [('MEDIA-ZEO-25',20),('VALV-BORB-E2',6),('CURVA-PVC-90-2',12),('TUBO-PVC-2',2)]:
        add_k(k, m, q)
# KITS HIDRAULICOS (Todos os 150mm)
for k in ['KIT-HID-4272-PV-150MM', 'KIT-HID-4872-PV-150MM', 'KIT-HID-6380-PV-150MM']:
    for m,q in [('MEDIA-ZEO-25',60),('VALV-BORB-E6',6),('CURVA-PVC-90-6',12),('TUBO-PVC-6',2)]:
        add_k(k, m, q)


# --- CARREGAR DATAFRAMES ---
db = {k: pd.DataFrame(v) for k, v in DEFAULT_DATA.items()}


# ==============================================================================
# 3. MOTOR DE CÁLCULO EM TEMPO REAL
# ==============================================================================
def calcular_orcamento(num_vasos, tam_vaso, diametro, margens_dict):
    df_mat = db["Materiais"]
    df_mdo = db["MaoDeObra"]
    df_kits = db["Kits"]
    df_conf_acion = db["Config_Acionamentos"]
    df_conf_vasos = db["Config_Vasos"]
    df_conf_hidra = db["Config_Hidraulica"]

    # Regras
    try:
        regra_painel = df_conf_acion[df_conf_acion['Num_Vasos'] == num_vasos].iloc[0]
        regra_vaso = df_conf_vasos[df_conf_vasos['Descricao_Vaso'] == tam_vaso].iloc[0]
        filtro_hid = (df_conf_hidra['Descricao_Vaso'] == tam_vaso) & (df_conf_hidra['ID_Diametro_mm'] == diametro)
        
        if filtro_hid.sum() == 0: return None, "Combinação Inválida"
        
        id_kit_hidra = df_conf_hidra[filtro_hid].iloc[0]['ID_Kit_Hidraulico_p_Vaso']
        id_kit_painel = regra_painel['ID_Kit_Painel_Eletrico']
    except:
        return None, "Erro ao buscar regras"

    itens = []
    # 1. Itens Soltos
    itens.append({'ID': regra_painel['ID_Material_CLP'], 'Qtd': 1, 'Tipo': 'Material'})
    itens.append({'ID': regra_painel['ID_Material_Painel'], 'Qtd': 1, 'Tipo': 'Material'})
    itens.append({'ID': regra_painel['ID_Material_IHM'], 'Qtd': 1, 'Tipo': 'Material'})
    itens.append({'ID': regra_vaso['ID_Material_Vaso'], 'Qtd': num_vasos, 'Tipo': 'Material'})

    # 2. Kits (Painel e Hidráulica)
    for k, fator in [(id_kit_painel, 1), (id_kit_hidra, num_vasos)]:
        for _, r in df_kits[df_kits['ID_Kit'] == k].iterrows():
            itens.append({'ID': r['ID_Material'], 'Qtd': r['Quantidade'] * fator, 'Tipo': 'Material'})

    # 3. Mão de Obra
    itens.append({'ID': 'MDO-MONT-ELET', 'Qtd': regra_painel['Horas_MDO_Mont_Elet'], 'Tipo': 'MDO'})
    itens.append({'ID': 'MDO-PROG-CLP', 'Qtd': regra_painel['Horas_MDO_Prog_CLP'], 'Tipo': 'MDO'})
    itens.append({'ID': 'MDO-MONT-HIDR', 'Qtd': regra_vaso['Horas_MDO_Hidr_p_Vaso'] * num_vasos, 'Tipo': 'MDO'})

    resultado = []
    custo_total_projeto = 0
    venda_total_projeto = 0

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

        margem = margens_dict.get(grupo, 0.5)
        
        total_custo = custo * item['Qtd']
        total_venda = total_custo * (1 + margem)

        resultado.append({
            'Descrição': desc,
            'Grupo': grupo,
            'Qtd': item['Qtd'],
            'Custo Unit': custo,
            'Preço Venda': total_venda
        })
        
        custo_total_projeto += total_custo
        venda_total_projeto += total_venda

    df_final = pd.DataFrame(resultado)
    return df_final, custo_total_projeto, venda_total_projeto

# ==============================================================================
# 4. INTERFACE VISUAL (REPLICAÇÃO DO PRINT)
# ==============================================================================

st.title("Simulador de Orçamento")

# --- 1. FILTROS SUPERIORES (3 COLUNAS) ---
# Não usamos st.sidebar para ficar igual ao print
c1, c2, c3 = st.columns(3)

with c1:
    sel_vasos = st.selectbox("Nº de Vasos", [1, 2, 3, 4], index=3)

with c2:
    sel_tamanho = st.selectbox("Tamanho do Vaso", db["Config_Vasos"]['Descricao_Vaso'].unique(), index=3)

with c3:
    sel_diametro = st.selectbox("Diâmetro da Tubulação", db["Config_Hidraulica"]['ID_Diametro_mm'].unique(), index=1)

st.divider()

# --- 2. SLIDERS DE MARGEM (LINHA ÚNICA) ---
st.caption("Parâmetros de Margem de Lucro (%)")
m1, m2, m3, m4, m5 = st.columns(5)

# Valores iniciais padrão 50% (0.50)
margem_clp = m1.slider("Margem CLP", 0, 100, 50) / 100
margem_hidra = m2.slider("Margem Hidráulica", 0, 100, 50) / 100
margem_painel = m3.slider("Margem Painel", 0, 100, 50) / 100
margem_mdo = m4.slider("Margem MDO", 0, 100, 50) / 100
margem_vasos = m5.slider("Margem Vasos", 0, 100, 50) / 100

# Monta o dicionário para o cálculo
MARGENS = {
    "CLP": margem_clp,
    "Hidráulica": margem_hidra,
    "Itens de Painel": margem_painel,
    "Mão de Obra": margem_mdo,
    "Vasos": margem_vasos
}

# --- 3. CÁLCULO AUTOMÁTICO (SEM BOTÃO) ---
# O Streamlit roda o script inteiro sempre que um selectbox ou slider muda.
# Então o cálculo acontece em tempo real aqui:

df_resultado, custo_total, venda_total = calcular_orcamento(sel_vasos, sel_tamanho, sel_diametro, MARGENS)

if df_resultado is None:
    st.error("❌ Combinação de Tamanho de Vaso e Diâmetro não cadastrada no sistema.")
else:
    # Cálculos Finais
    margem_reais = venda_total - custo_total
    margem_percentual = (margem_reais / custo_total) * 100 if custo_total > 0 else 0

    # --- 4. CARTÕES DE KPI (4 COLUNAS) ---
    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Preço de Venda Total", f"R$ {venda_total:,.2f}")
    k2.metric("Custo Total Projeto", f"R$ {custo_total:,.2f}")
    k3.metric("Margem Total (R$)", f"R$ {margem_reais:,.2f}")
    k4.metric("Margem %", f"{margem_percentual:.1f}%")

    st.divider()

    # --- 5. TABELA DETALHADA ---
    st.subheader("Detalhamento dos Itens")
    
    # Formatação para exibição
    df_show = df_resultado.copy()
    df_show['Custo Unit'] = df_show['Custo Unit'].map('R$ {:,.2f}'.format)
    df_show['Preço Venda'] = df_show['Preço Venda'].map('R$ {:,.2f}'.format)
    
    st.dataframe(
        df_show[['Descrição', 'Grupo', 'Qtd', 'Custo Unit', 'Preço Venda']],
        use_container_width=True,
        height=500 # Altura fixa para parecer uma lista longa
    )
