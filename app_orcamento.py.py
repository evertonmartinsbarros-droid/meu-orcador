import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import tempfile
import os

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTILO
# ==============================================================================
st.set_page_config(page_title="Gerador de Propostas", page_icon="💼", layout="wide")

st.markdown("""
<style>
    /* Estilo dos Cartões (KPIs) */
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
    .stDataFrame { border: 1px solid #ddd; }
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
        'ID_Material': ['CLP-AUT-01', 'PAINEL-8060', 'CONT-MOT-12A', 'VASO-FIL-3072', 'VALV-BORB-E2', 'TUBO-PVC-2', 'MDO-MONT-ELET'],
        'Descricao': ['CLP Básico', 'Painel 80x60', 'Contator 12A', 'Vaso 30x72', 'Válvula 2pol', 'Tubo 2pol', 'Montagem'],
        'Grupo_Orcamento': ['CLP', 'Itens de Painel', 'Itens de Painel', 'Vasos', 'Hidráulica', 'Hidráulica', 'Mão de Obra'],
        'Preco_Custo': [2500.0, 750.0, 90.0, 6000.0, 700.0, 90.0, 80.0]
    },
    "MaoDeObra": {
        'ID_MaoDeObra': ['MDO-MONT-ELET', 'MDO-PROG-CLP', 'MDO-MONT-HIDR'],
        'Tipo_Servico': ['Montagem Elétrica', 'Programação CLP', 'Montagem Hidráulica'],
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
    "Kits": {'ID_Kit': [], 'ID_Material': [], 'Quantidade': []}
}

# --- FUNÇÕES AUXILIARES ---
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
    st.toast(f"✅ {key} salvo!", icon="💾")

# Carrega dados
db = load_data()

# ==============================================================================
# 3. CLASSE PDF PROFISSIONAL
# ==============================================================================
class PropostaPDF(FPDF):
    def __init__(self, empresa_dados, cliente_dados, logo_path=None):
        super().__init__()
        self.empresa = empresa_dados
        self.cliente = cliente_dados
        self.logo_path = logo_path

    def header(self):
        # Logo
        if self.logo_path:
            try:
                self.image(self.logo_path, 10, 8, 33)
            except: pass
        
        # Dados da Empresa (Alinhado à Direita)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 5, self.empresa['nome'], 0, 1, 'R')
        self.set_font('Arial', '', 9)
        self.cell(0, 5, self.empresa['endereco'], 0, 1, 'R')
        self.cell(0, 5, f"Tel: {self.empresa['telefone']} | Email: {self.empresa['email']}", 0, 1, 'R')
        self.cell(0, 5, self.empresa['site'], 0, 1, 'R')
        self.ln(10)
        
        # Título
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 51, 102) # Azul escuro
        self.cell(0, 10, 'PROPOSTA COMERCIAL', 0, 1, 'C')
        self.ln(5)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def chapter_info_cliente(self):
        self.set_fill_color(240, 240, 240)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, " DADOS DO CLIENTE", 1, 1, 'L', 1)
        self.set_font('Arial', '', 10)
        self.cell(0, 6, f"Cliente: {self.cliente['nome']}", 0, 1)
        self.cell(0, 6, f"Projeto: {self.cliente['projeto']}", 0, 1)
        self.cell(0, 6, f"Data: {datetime.now().strftime('%d/%m/%Y')} | Validade: {self.cliente['validade']}", 0, 1)
        self.ln(5)

    def chapter_tabela(self, df):
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 9)
        # Cabeçalho
        self.cell(100, 8, "Item / Descrição", 1, 0, 'L', 1)
        self.cell(20, 8, "Qtd", 1, 0, 'C', 1)
        self.cell(35, 8, "Unitário (R$)", 1, 0, 'R', 1)
        self.cell(35, 8, "Total (R$)", 1, 1, 'R', 1)
        
        # Dados
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 9)
        fill = False
        for _, row in df.iterrows():
            self.set_fill_color(245, 245, 245)
            self.cell(100, 7, str(row['Descrição'])[0:55], 1, 0, 'L', fill)
            self.cell(20, 7, str(row['Qtd']), 1, 0, 'C', fill)
            self.cell(35, 7, f"{row['Venda Unit']:,.2f}", 1, 0, 'R', fill)
            self.cell(35, 7, f"{row['Total Venda']:,.2f}", 1, 1, 'R', fill)
            fill = not fill # Alternar cor das linhas
        
        self.ln(2)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"VALOR TOTAL: R$ {df['Total Venda'].sum():,.2f}", 0, 1, 'R')
        self.ln(5)

    def chapter_condicoes(self):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, " CONDIÇÕES COMERCIAIS", 1, 1, 'L', 1)
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, f"Prazo de Entrega: {self.cliente['prazo']}")
        self.multi_cell(0, 6, f"Pagamento: {self.cliente['pagamento']}")
        self.ln(20)
        
        # Assinaturas
        self.set_font('Arial', '', 10)
        y = self.get_y()
        self.line(20, y, 90, y)
        self.line(120, y, 190, y)
        self.cell(95, 5, self.empresa['nome'], 0, 0, 'C')
        self.cell(95, 5, "De Acordo (Cliente)", 0, 1, 'C')


# ==============================================================================
# 4. LÓGICA DE CÁLCULO
# ==============================================================================
def calcular_itens(num_vasos, tam_vaso, diametro, margens_dict):
    try:
        regra_painel = db["Config_Acionamentos"][db["Config_Acionamentos"]['Num_Vasos'] == num_vasos].iloc[0]
        regra_vaso = db["Config_Vasos"][db["Config_Vasos"]['Descricao_Vaso'] == tam_vaso].iloc[0]
        df_hidra = db["Config_Hidraulica"]
        filtro_hid = (df_hidra['Descricao_Vaso'] == tam_vaso) & (df_hidra['ID_Diametro_mm'] == diametro)
        
        if filtro_hid.sum() == 0: return None
        
        id_kit_hidra = df_hidra[filtro_hid].iloc[0]['ID_Kit_Hidraulico_p_Vaso']
        id_kit_painel = regra_painel['ID_Kit_Painel_Eletrico']

        itens = []
        # Base
        itens.append({'ID': regra_painel['ID_Material_CLP'], 'Qtd': 1, 'Tipo': 'Material'})
        itens.append({'ID': regra_painel['ID_Material_Painel'], 'Qtd': 1, 'Tipo': 'Material'})
        itens.append({'ID': regra_painel['ID_Material_IHM'], 'Qtd': 1, 'Tipo': 'Material'})
        itens.append({'ID': regra_vaso['ID_Material_Vaso'], 'Qtd': num_vasos, 'Tipo': 'Material'})
        
        # Kits
        df_kits = db["Kits"]
        for k, f in [(id_kit_painel, 1), (id_kit_hidra, num_vasos)]:
            k_itens = df_kits[df_kits['ID_Kit'] == k]
            for _, r in k_itens.iterrows():
                itens.append({'ID': r['ID_Material'], 'Qtd': r['Quantidade'] * f, 'Tipo': 'Material'})

        # MDO
        itens.append({'ID': 'MDO-MONT-ELET', 'Qtd': regra_painel['Horas_MDO_Mont_Elet'], 'Tipo': 'MDO'})
        itens.append({'ID': 'MDO-PROG-CLP', 'Qtd': regra_painel['Horas_MDO_Prog_CLP'], 'Tipo': 'MDO'})
        itens.append({'ID': 'MDO-MONT-HIDR', 'Qtd': regra_vaso['Horas_MDO_Hidr_p_Vaso'] * num_vasos, 'Tipo': 'MDO'})

        # Preços
        res = []
        df_mat, df_mdo = db["Materiais"], db["MaoDeObra"]

        for item in itens:
            if item['Tipo'] == 'Material':
                d = df_mat[df_mat['ID_Material'] == item['ID']]
                if d.empty: continue
                desc = d.iloc[0]['Descricao']
                grp = d.iloc[0]['Grupo_Orcamento']
                cust = float(d.iloc[0]['Preco_Custo'])
                mrg = margens_dict.get(grp, 0)
            else:
                d = df_mdo[df_mdo['ID_MaoDeObra'] == item['ID']]
                if d.empty: continue
                desc = d.iloc[0]['Tipo_Servico']
                grp = "Mão de Obra"
                cust = float(d.iloc[0]['Custo_Hora'])
                if item['ID'] == 'MDO-MONT-ELET': mrg = margens_dict.get("MDO_Elet", 0)
                elif item['ID'] == 'MDO-PROG-CLP': mrg = margens_dict.get("MDO_Prog", 0)
                elif item['ID'] == 'MDO-MONT-HIDR': mrg = margens_dict.get("MDO_Hidr", 0)
                else: mrg = 0

            unit_venda = cust * (1 + (mrg/100))
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
# 5. INTERFACE
# ==============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏢 Dados da Empresa")
    
    # Upload de Logo
    emp_logo = st.file_uploader("Logotipo", type=['png', 'jpg', 'jpeg'])
    if emp_logo:
        st.image(emp_logo, caption="Pré-visualização da Logo", use_container_width=True)

    with st.expander("Editar Cabeçalho PDF", expanded=False):
        emp_nome = st.text_input("Nome Empresa", "Sua Empresa Ltda")
        emp_end = st.text_input("Endereço", "Rua Exemplo, 123")
        emp_tel = st.text_input("Telefone", "(11) 99999-9999")
        emp_email = st.text_input("Email", "contato@empresa.com")
        emp_site = st.text_input("Site", "www.empresa.com")

    st.divider()
    st.header("⚠️ Zona de Perigo")
    if 'reset_confirm' not in st.session_state: st.session_state.reset_confirm = False
    
    if st.button("Restaurar Padrão"): st.session_state.reset_confirm = True
    
    if st.session_state.reset_confirm:
        st.warning("Tem certeza?")
        c_sim, c_nao = st.columns(2)
        if c_sim.button("✅ SIM"):
            load_data(force_reset=True)
            st.session_state.reset_confirm = False
            st.rerun()
        if c_nao.button("❌ NÃO"):
            st.session_state.reset_confirm = False
            st.rerun()

# --- ABAS ---
tab_dash, tab_kits, tab_db = st.tabs(["📊 Gerador de Proposta", "🛠️ Editor de Kits", "🗃️ Banco de Preços"])

# ---------------- ABA 1: DASHBOARD ----------------
with tab_dash:
    st.title("Gerador de Proposta Comercial")
    
    # Inputs
    c1, c2, c3 = st.columns(3)
    with c1: sel_vasos = st.selectbox("Nº Vasos", [1,2,3,4], index=3)
    with c2: sel_tamanho = st.selectbox("Tamanho Vaso", db["Config_Vasos"]['Descricao_Vaso'].unique(), index=3)
    with c3: sel_diametro = st.selectbox("Diâmetro Tubo", db["Config_Hidraulica"]['ID_Diametro_mm'].unique(), index=1)
    
    st.divider()
    
    # Margens
    st.subheader("Margens de Lucro (%)")
    col_m = st.columns(7)
    m_clp = col_m[0].number_input("CLP", 0, 500, 50, step=1)
    m_painel = col_m[1].number_input("Painel", 0, 500, 50, step=1)
    m_hidra = col_m[2].number_input("Peças Hidr.", 0, 500, 50, step=1)
    m_vasos = col_m[3].number_input("Vasos", 0, 500, 50, step=1)
    m_elet = col_m[4].number_input("MDO Elét.", 0, 500, 50, step=1)
    m_prog = col_m[5].number_input("MDO Prog.", 0, 500, 50, step=1)
    m_mont_h = col_m[6].number_input("MDO Hidr.", 0, 500, 50, step=1)

    MARGENS = {
        "CLP": m_clp, "Itens de Painel": m_painel, "Hidráulica": m_hidra, "Vasos": m_vasos,
        "MDO_Elet": m_elet, "MDO_Prog": m_prog, "MDO_Hidr": m_mont_h
    }
    
    df_inicial = calcular_itens(sel_vasos, sel_tamanho, sel_diametro, MARGENS)
    
    if df_inicial is None:
        st.error("❌ Configuração técnica não encontrada.")
    else:
        # 1. Exibe KPIs (Cartões)
        # Mas primeiro precisamos saber os totais dos itens marcados.
        # O Streamlit reexecuta o código, então pegamos o df_editado (estado atual)
        # Porém, antes da tabela ser editada, usamos o df_inicial.
        # Para os cartões aparecerem ANTES da tabela e reagirem, precisamos processar a tabela primeiro na lógica visual?
        # Não, o ideal é mostrar os valores PADRÃO primeiro, ou colocar os cartões DEPOIS da tabela para reagirem ao checkbox.
        # Vou colocar DEPOIS da tabela para ser dinâmico com o checkbox, ou antes assumindo tudo marcado.
        # Pela UX, melhor colocar DEPOIS da tabela ou usar session_state (complexo).
        # Vou colocar LOGO ABAIXO das margens, assumindo TUDO MARCADO inicialmente,
        # e depois atualizo uma area de "Resultado Final" abaixo da tabela.
        
        # Vamos criar uma área de RESULTADO DINÂMICO após a tabela.
        
        st.divider()
        st.subheader("Itens do Orçamento")
        
        df_editado = st.data_editor(
            df_inicial,
            column_config={
                "Incluir": st.column_config.CheckboxColumn("Incluir", width="small"),
                "Custo Unit": st.column_config.NumberColumn(format="R$ %.2f"),
                "Venda Unit": st.column_config.NumberColumn(format="R$ %.2f"),
                "Total Venda": st.column_config.NumberColumn(format="R$ %.2f"),
                "Total Custo": None 
            },
            disabled=["Descrição", "Grupo", "Qtd", "Custo Unit", "Venda Unit", "Total Venda"],
            hide_index=True,
            use_container_width=True
        )
        
        # Cálculo Final (Baseado no Checkbox)
        df_final = df_editado[df_editado['Incluir'] == True].copy()
        venda_total = df_final['Total Venda'].sum()
        custo_total = df_final['Total Custo'].sum()
        lucro = venda_total - custo_total
        lucro_pct = (lucro / custo_total * 100) if custo_total > 0 else 0
        
        # --- CARTÕES (KPIs) VOLTARAM AQUI ---
        st.divider()
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Valor Final", f"R$ {venda_total:,.2f}")
        k2.metric("Custo Estimado", f"R$ {custo_total:,.2f}")
        k3.metric("Lucro R$", f"R$ {lucro:,.2f}")
        k4.metric("Margem Real %", f"{lucro_pct:.1f}%")
        # -------------------------------------
        
        # Dados Cliente
        with st.expander("📝 Preencher Dados do Cliente para PDF", expanded=True):
            col_c1, col_c2 = st.columns(2)
            cli_nome = col_c1.text_input("Nome do Cliente", "Cliente Exemplo")
            cli_proj = col_c2.text_input("Nome do Projeto/Obra", "ETA 01")
            
            col_c3, col_c4, col_c5 = st.columns(3)
            cli_validade = col_c3.date_input("Validade Proposta", datetime.now() + timedelta(days=15))
            cli_prazo = col_c4.text_input("Prazo de Entrega", "30 dias após pedido")
            cli_pagto = col_c5.text_input("Pagamento", "50% Sinal / 50% Entrega")
        
        # Botão PDF
        if st.button("📄 GERAR PROPOSTA PDF", type="primary"):
            logo_tmp = None
            if emp_logo:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                    f.write(emp_logo.read())
                    logo_tmp = f.name
            
            dados_empresa = {'nome': emp_nome, 'endereco': emp_end, 'telefone': emp_tel, 'email': emp_email, 'site': emp_site}
            dados_cliente = {
                'nome': cli_nome, 'projeto': cli_proj, 
                'validade': cli_validade.strftime('%d/%m/%Y'),
                'prazo': cli_prazo, 'pagamento': cli_pagto
            }
            
            pdf = PropostaPDF(dados_empresa, dados_cliente, logo_tmp)
            pdf.add_page()
            pdf.header()
            pdf.chapter_info_cliente()
            pdf.chapter_tabela(df_final)
            pdf.chapter_condicoes()
            
            pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf.output(pdf_file.name)
            
            with open(pdf_file.name, "rb") as f:
                st.download_button("📥 Baixar Arquivo PDF", f, f"Proposta_{cli_nome}.pdf", mime="application/pdf")
            
            if logo_tmp: os.remove(logo_tmp)

# ---------------- ABA 2: EDITOR DE KITS ----------------
with tab_kits:
    st.header("🛠️ Editor de Kits")
    st.info("💡 Para remover um item, selecione a linha e pressione **Delete** no teclado.")
    
    kits = sorted(db["Kits"]['ID_Kit'].unique())
    col_k1, col_k2 = st.columns([2,1])
    kit_sel = col_k1.selectbox("Selecione o Kit:", kits)
    
    novo_kit = col_k2.text_input("Ou crie novo (ID):")
    if col_k2.button("Criar Kit") and novo_kit:
        if novo_kit not in kits:
            db["Kits"] = pd.concat([db["Kits"], pd.DataFrame({'ID_Kit':[novo_kit],'ID_Material':[''],'Quantidade':[0]})])
            save_data("Kits", db["Kits"])
            st.rerun()
    
    if novo_kit in kits: kit_sel = novo_kit
    
    df_k = db["Kits"][db["Kits"]['ID_Kit'] == kit_sel].copy()
    df_materiais = db["Materiais"][['ID_Material', 'Descricao']]
    df_view = pd.merge(df_k, df_materiais, on='ID_Material', how='left')
    
    st.subheader(f"Itens: {kit_sel}")
    df_edited = st.data_editor(
        df_view[['ID_Material', 'Descricao', 'Quantidade']],
        column_config={
            "ID_Material": st.column_config.TextColumn(disabled=True),
            "Descricao": st.column_config.TextColumn(disabled=True),
            "Quantidade": st.column_config.NumberColumn(min_value=0.0)
        },
        num_rows="dynamic",
        key="editor_kits_main",
        use_container_width=True
    )
    
    if st.button("💾 Salvar Alterações no Kit"):
        db["Kits"] = db["Kits"][db["Kits"]['ID_Kit'] != kit_sel]
        novos_dados = df_edited.copy()
        novos_dados['ID_Kit'] = kit_sel
        novos_dados = novos_dados[novos_dados['ID_Material'] != '']
        db["Kits"] = pd.concat([db["Kits"], novos_dados[['ID_Kit', 'ID_Material', 'Quantidade']]], ignore_index=True)
        save_data("Kits", db["Kits"])
        st.success("Kit atualizado!")
        st.rerun()
    
    st.divider()
    st.markdown("#### Adicionar Novo Item ao Kit")
    c_add1, c_add2, c_add3 = st.columns([3, 1, 1])
    opts = df_materiais.apply(lambda x: f"{x['Descricao']} | {x['ID_Material']}", axis=1)
    item_add = c_add1.selectbox("Item:", opts)
    qtd_add = c_add2.number_input("Qtd:", 1.0)
    
    if c_add3.button("➕ Adicionar"):
        id_mat = item_add.split(" | ")[-1]
        novo_reg = pd.DataFrame({'ID_Kit': [kit_sel], 'ID_Material': [id_mat], 'Quantidade': [qtd_add]})
        db["Kits"] = pd.concat([db["Kits"], novo_reg], ignore_index=True)
        save_data("Kits", db["Kits"])
        st.rerun()

# ---------------- ABA 3: BANCO DE DADOS ----------------
with tab_db:
    st.header("🗃️ Banco de Preços")
    tab_sel = st.selectbox("Tabela:", list(FILES.keys()))
    df_db_edited = st.data_editor(db[tab_sel], num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Alterações no Banco de Dados"):
        save_data(tab_sel, df_db_edited); st.rerun()
