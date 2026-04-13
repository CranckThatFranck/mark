import os
import signal
import psutil
import logging
from state import global_state

logger = logging.getLogger(__name__)

class ProcessManager:
    """
    Gerencia a interrupção segura dos subprocessos criados pelo Open Interpreter.
    Quando uma tarefa é interrompida via Kill Switch, precisamos garantir que:
    1. A thread/processo gerador seja parado
    2. Qualquer script ou comando filho gerado por ele (ex: processos longos) seja morto
    """
    
    @staticmethod
    def kill_process_tree(pid: int):
        """
        Encerra o processo pai e todos os processos filhos de forma recursiva.
        """
        if not pid:
            return
            
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Tenta terminar os filhos primeiro (SIGTERM)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
                    
            # Se não morrerem, kill -9
            gone, still_alive = psutil.wait_procs(children, timeout=3)
            for child in still_alive:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
                    
            # Finalmente encerra o pai
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass
                    
            logger.info(f"Árvore de processos do PID {pid} encerrada.")
        except psutil.NoSuchProcess:
            logger.info(f"Processo {pid} já não existe.")
        except Exception as e:
            logger.error(f"Erro ao encerrar árvore do PID {pid}: {e}")

    @staticmethod
    def kill_pgid(pgid: int):
        """
        Mata todo o grupo de processos (Process Group ID).
        Ideal para limpar subprocessos desgarrados no Linux.
        """
        if not pgid:
            return
            
        try:
            # Envia SIGTERM para todo o grupo
            os.killpg(pgid, signal.SIGTERM)
            logger.info(f"Sinal SIGTERM enviado ao PGID {pgid}")
            
            # Futuro: poderia colocar um timer e mandar SIGKILL
        except ProcessLookupError:
            logger.info(f"PGID {pgid} não encontrado ou já encerrado.")
        except Exception as e:
            logger.error(f"Erro ao encerrar PGID {pgid}: {e}")

