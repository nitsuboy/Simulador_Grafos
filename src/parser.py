import re

def _parse_linha_tropa(linha):
    """Traduz uma única linha de comando de tropa no formato '<id> <forca>: <rota>'."""
    try:
        parte_info, parte_rota = [p.strip() for p in linha.split(':')]
        info_tropa = parte_info.split()
        
        if len(info_tropa) != 2:
            print(f"AVISO: Formato de info de tropa inválido: '{parte_info}'. Esperado '<id> <forca>'. Linha ignorada.")
            return None
            
        id_tropa = info_tropa[0]
        forca = int(info_tropa[1])
        
        comandos = []
        passos_str = [p.strip() for p in parte_rota.split('->')]
        
        for passo in passos_str[1:]:  # Ignora o primeiro passo, que é o ID e força
            partes_passo = passo.strip().split()
            comando_tipo = partes_passo[0]
            
            if comando_tipo == 'ataca' and len(partes_passo) > 1:
                comandos.append({'tipo': 'ATACAR', 'alvo': partes_passo[1]})
            elif comando_tipo == 'permanece':
                comandos.append({'tipo': 'PERMANECER'})
            elif comando_tipo == 'recua':
                comandos.append({'tipo': 'RECUAR'})
            else:
                comandos.append({'tipo': 'MOVER', 'alvo': comando_tipo})
        
        return {'id': id_tropa, 'forca': forca, 'comandos': comandos}
    except (ValueError, IndexError):
        print(f"AVISO: Erro de formatação na linha de tropa: '{linha}'. Linha ignorada.")
        return None

def _parse_linha_transporte(linha):
    """Traduz uma única linha de comando de transporte."""
    try:
        # Expressão regular para capturar os dados da missão de forma robusta
        padrao = re.compile(r"missao:\s*COLETAR\s+(MAX|\d+)\s+DE\s+([\w_]+),\s*ENTREGAR\s+EM\s+([\w_]+)", re.IGNORECASE)
        match = padrao.match(linha)
        
        if not match:
            print(f"AVISO: Formato de missão de transporte inválido: '{linha}'. Linha ignorada.")
            return None
        
        quantidade_str, origem, destino = match.groups()
        quantidade = 'MAX' if quantidade_str.upper() == 'MAX' else int(quantidade_str)
        
        fila_de_comandos = [
            {'tipo': 'COLETAR', 'alvo': origem, 'quantidade': quantidade},
            {'tipo': 'ENTREGAR', 'alvo': destino}
        ]
        return fila_de_comandos
    except (ValueError, IndexError):
        print(f"AVISO: Erro de formatação na linha de transporte: '{linha}'. Linha ignorada.")
        return None

def parse_string_de_ordens(texto_das_ordens):
    """
    Função principal do parser. Recebe uma STRING com as ordens de um jogador
    e a traduz para um dicionário estruturado.
    """
    if not isinstance(texto_das_ordens, str):
        print("AVISO: A IA não retornou uma string de ordens. Ignorando.")
        return {"novas_tropas": [], "transporte": None}

    ordens = {"novas_tropas": [], "transporte": None}
    
    secao_atual = None
    # Itera sobre as linhas da string de ordens
    for linha in texto_das_ordens.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith('#'): continue
        
        if "Novas Tropas:" in linha:
            secao_atual = "TROPAS"
            continue
        elif "Transporte:" in linha:
            secao_atual = "TRANSPORTE"
            continue

        if secao_atual == "TROPAS":
            ordem_tropa = _parse_linha_tropa(linha)
            if ordem_tropa:
                ordens["novas_tropas"].append(ordem_tropa)
        elif secao_atual == "TRANSPORTE":
            ordem_transporte = _parse_linha_transporte(linha)
            if ordem_transporte:
                ordens["transporte"] = ordem_transporte
    
    return ordens