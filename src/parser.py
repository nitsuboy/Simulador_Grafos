import re

def _parse_linha_tropa(linha):
    """Traduz uma única linha de comando de tropa no novo formato."""
    try:
        parte_info, parte_rota = [p.strip() for p in linha.split(':')]
        
        info_tropa = parte_info.split()
        
        # Validação: o comando para uma tropa deve ter exatamente 2 parâmetros (id e forca).
        if len(info_tropa) != 2:
            print(f"AVISO: Formato de info de tropa inválido: '{parte_info}'. Esperado '<id> <forca>'. Linha ignorada.")
            return None
            
        id_tropa = info_tropa[0]
        forca = int(info_tropa[1])
        
        comandos = []
        passos_str = [p.strip() for p in parte_rota.split('->')]
        
        for passo in passos_str:
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
        padrao = re.compile(r"missao:\s*COLETAR\s+(MAX|\d+)\s+DE\s+(\w+),\s*ENTREGAR\s+EM\s+(\w+)", re.IGNORECASE)
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

def parse_ordens_jogador(jogador_id):
    """
    Lê o arquivo de ordens de um jogador
    e o traduz para um dicionário estruturado.
    """
    ordens = {"novas_tropas": [], "transporte": None}
    nome_arquivo = f"ordens_{jogador_id}.txt"
    
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as f:
            secao_atual = None
            for linha in f:
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

    except FileNotFoundError:
        print(f"AVISO: Arquivo de ordens '{nome_arquivo}' não encontrado para o jogador {jogador_id}.")
    
    return ordens