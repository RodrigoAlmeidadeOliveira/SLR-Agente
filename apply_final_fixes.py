import os
import re

cap3_path = "cap3_slr_revised.tex"

def main():
    if not os.path.exists(cap3_path):
        print(f"❌ Erro: {cap3_path} não encontrado no diretório atual.")
        return

    with open(cap3_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Sync Kappa Prose (n=468 vs n=420)
    # Procura a menção antiga e atualiza com os números processados e a justificativa
    kappa_pattern = r"(A stratified random 20\\% sample of T/A\s*)\(\s*n\s*=\s*468\s*\)(.*?)was independently re-rated"
    kappa_repl = r"\1(a target of $n = 468$) \2was selected for independent re-rating. From the T/A sample, 420 papers were effectively processed, as some were excluded due to missing abstracts or API constraints"
    content = re.sub(kappa_pattern, kappa_repl, content, flags=re.IGNORECASE)

    # 2. Reconcile screen-blanks (186 -> 238)
    # Atualiza o número de papers sem abstract com base no script executado
    content = re.sub(r"186(\s+remaining\s+no-abstract)", r"238\1", content)
    
    # 3. Add human spot-check declaration in Internal Validity
    spot_check_text = (
        "\n\nTo further strengthen the reliability of the screening process, a human spot-check of rating disagreements "
        "is planned. A sample of approximately 50 papers where the two primary reviewers disagreed on the final decision "
        "(include/exclude) will be analyzed by a third senior researcher to identify the root cause of the disagreement "
        "(e.g., criteria ambiguity, reviewer error). The findings from this analysis will be incorporated into the "
        "camera-ready version of this work to provide a qualitative assessment of reviewer alignment."
    )
    if "human spot-check" not in content:
        # Adiciona a declaração logo após a abertura da subseção
        content = re.sub(r"(\\subsection\{Internal Validity\})", r"\1" + spot_check_text, content)

    with open(cap3_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Arquivo {cap3_path} atualizado com sucesso!")

if __name__ == "__main__":
    main()