import os
from ftplib import FTP, error_perm
from typing import Optional, Tuple, List, Dict
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
import threading


FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASSWORD = os.getenv("FTP_PASSWORD")
FTP_BASE_DIR = os.getenv("FTP_BASE_DIR")
FTP_PUBLIC_BASE_URL = os.getenv("FTP_PUBLIC_BASE_URL", "")

# Cache para metadatos de archivos (optimización de rendimiento)
_file_metadata_cache: Dict[str, Dict] = {}
_cache_lock = threading.Lock()
CACHE_DURATION_MINUTES = 5  # Cache válido por 5 minutos


# =====================================================
# FUNCIONES HELPER Y CONTEXT MANAGERS
# =====================================================

def _validate_ftp_credentials() -> bool:
    """Valida que las credenciales FTP estén configuradas."""
    return all([FTP_HOST, FTP_USER, FTP_PASSWORD])


def _build_remote_path(subdir: str) -> str:
    """Construye la ruta remota completa para un subdirectorio."""
    if FTP_BASE_DIR:
        return f"{FTP_BASE_DIR.rstrip('/')}/{subdir.strip('/')}"
    return subdir.strip('/')


def _filter_valid_files(files: List[str]) -> List[str]:
    """Filtra y devuelve solo nombres de archivos válidos (no carpetas)."""
    result = []
    for f in files:
        if f and not f.endswith('/') and f not in ['.', '..']:
            filename = os.path.basename(f)
            if filename not in ['.', '..']:
                result.append(filename)
    return result


def _format_file_size(size_bytes: int) -> str:
    """Convierte bytes a formato legible (KB, MB, GB)."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


@contextmanager
def ftp_connection():
    """
    Context manager para manejar conexiones FTP de forma segura.
    
    Yields:
        FTP: Conexión FTP autenticada
        
    Raises:
        ConnectionError: Si no se pueden validar las credenciales o conectar
    """
    if not _validate_ftp_credentials():
        raise ConnectionError("Faltan credenciales FTP requeridas")
    
    ftp = None
    try:
        ftp = FTP(timeout=30)  # Timeout de 30 segundos
        ftp.connect(FTP_HOST, 21)  # Puerto FTP estándar
        ftp.login(FTP_USER, FTP_PASSWORD)
        yield ftp
    except OSError as e:
        if "Network is unreachable" in str(e):
            raise ConnectionError(f"No se puede alcanzar el servidor FTP {FTP_HOST}. Verifique la configuración de DNS/red.")
        elif "Connection refused" in str(e):
            raise ConnectionError(f"Conexión rechazada por el servidor FTP {FTP_HOST}. Verifique que el servicio FTP esté funcionando.")
        else:
            raise ConnectionError(f"Error de red conectando a FTP: {e}")
    except Exception as e:
        raise ConnectionError(f"Error conectando a FTP: {e}")
    finally:
        if ftp:
            try:
                ftp.quit()
            except Exception:
                try:
                    ftp.close()
                except Exception:
                    pass


def _ensure_dirs(ftp: FTP, remote_dir: str) -> None:
    parts = [p for p in remote_dir.split('/') if p]
    current = ''
    for part in parts:
        current += '/' + part
        try:
            ftp.mkd(current)
        except error_perm as e:
            # 550 means already exists; ignore other errors
            if not str(e).startswith('550'):
                raise


def upload_file(local_path: str, remote_subdir: str, filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Sube un archivo vía FTP y retorna la URL pública si está configurada.

    Args:
        local_path: ruta local del archivo
        remote_subdir: subcarpeta relativa dentro de FTP_BASE_DIR (e.g. 'recientes' o 'anteriores')
        filename: nombre de archivo destino

    Returns:
        (public_url, remote_path) donde remote_path es la ruta absoluta en el servidor FTP
    """
    try:
        # Validar que el archivo local existe
        if not os.path.exists(local_path):
            print(f"❌ ERROR: Archivo local no existe: {local_path}")
            return None, None
        
        # Validar credenciales FTP
        if not _validate_ftp_credentials():
            print(f"❌ ERROR: Credenciales FTP no configuradas correctamente")
            return None, None
        
        # Construir ruta remota usando helper
        remote_dir = _build_remote_path(remote_subdir)
        remote_path = f"{remote_dir}/{filename}"
        
        print(f"🔍 DEBUG: Subiendo {local_path} -> {remote_path}")

        with ftp_connection() as ftp:
            _ensure_dirs(ftp, remote_dir)
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {remote_path}', f)
                print(f"✅ DEBUG: Archivo {filename} subido exitosamente a {remote_path}")

        # Construir URL pública si está configurada
        public_url = None
        if FTP_PUBLIC_BASE_URL:
            public_url = f"{FTP_PUBLIC_BASE_URL.rstrip('/')}/{remote_subdir.strip('/')}/{filename}"
        
        return public_url, remote_path
        
    except ConnectionError as e:
        print(f"❌ ERROR CONEXIÓN FTP: {e}")
        return None, None
    except FileNotFoundError as e:
        print(f"❌ ERROR ARCHIVO NO ENCONTRADO: {e}")
        return None, None
    except PermissionError as e:
        print(f"❌ ERROR PERMISOS: {e}")
        return None, None
    except Exception as e:
        print(f"❌ ERROR INESPERADO subiendo {filename}: {type(e).__name__}: {e}")
        return None, None


def download_to_temp(remote_path: str) -> Optional[str]:
    """
    Descarga un archivo del FTP a un archivo temporal y devuelve su ruta.
    remote_path debe ser absoluto (por ejemplo: /public_html/receipts/recientes/0001_123.pdf)
    """
    try:
        with ftp_connection() as ftp:
            # Crear archivo temporal
            suffix = os.path.splitext(remote_path)[1] or ".bin"
            fd, temp_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)

            with open(temp_path, 'wb') as f:
                ftp.retrbinary(f"RETR {remote_path}", f.write)
            return temp_path
            
    except Exception:
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        return None


def find_files_by_cedula(remote_subdir: str, cedula: str, with_metadata: bool = False) -> List:
    """
    Busca archivos PDF que contengan una cédula específica en su nombre.
    
    Este método es flexible y funciona con cualquier formato de nombre:
    - 0001_1192767555.pdf (CONSECUTIVO_CEDULA)
    - 1192767555.pdf (CEDULA)
    - 1192767555_0001.pdf (CEDULA_CONSECUTIVO)
    - PAGO_1192767555.pdf (TEXTO_CEDULA)
    
    Args:
        remote_subdir: Subcarpeta dentro de FTP_BASE_DIR (ej: 'recientes', 'anteriores')
        cedula: Número de cédula a buscar (solo números)
        with_metadata: Si True, devuelve metadatos completos. Si False, solo nombres.
    
    Returns:
        Lista de nombres de archivos PDF que contienen la cédula o metadatos completos
        
    Raises:
        ValueError: Si la cédula no es válida
        ConnectionError: Si no se puede conectar al FTP
    """
    # Validaciones de entrada
    if not cedula or not isinstance(cedula, str):
        raise ValueError("La cédula debe ser una cadena no vacía")
    
    if not cedula.isdigit():
        raise ValueError("La cédula debe contener solo números")
    
    if not remote_subdir or not isinstance(remote_subdir, str):
        raise ValueError("El subdirectorio debe ser una cadena no vacía")
    
    # Si se solicitan metadatos, usar la función optimizada
    if with_metadata:
        files_with_metadata = _get_files_with_metadata(remote_subdir)
        matching_files = []
        for file_info in files_with_metadata:
            if cedula in file_info["filename"]:
                matching_files.append(file_info)
        return matching_files
    
    # Comportamiento original para compatibilidad
    remote_dir = _build_remote_path(remote_subdir)
    
    try:
        with ftp_connection() as ftp:
            # Asegurar que el directorio existe
            _ensure_dirs(ftp, remote_dir)
            
            # OPTIMIZACIÓN: Intentar búsqueda directa con patrón
            try:
                # Intentar usar NLST con patrón para búsqueda más eficiente
                search_pattern = f"{remote_dir}/*{cedula}*.pdf"
                matching_files = ftp.nlst(search_pattern)
                
                # Si encontramos archivos, procesarlos
                if matching_files:
                    result = []
                    for file_path in matching_files:
                        filename = os.path.basename(file_path)
                        if filename and not filename.endswith('/'):
                            result.append(filename)
                    
                    if result:
                        result.sort()
                        return result
                
            except error_perm:
                # Si falla la búsqueda con patrón, usar método tradicional
                pass
            
            # FALLBACK: Método tradicional (más lento pero garantizado)
            try:
                all_files = ftp.nlst(remote_dir)
            except error_perm as e:
                if str(e).startswith('550'):
                    return []
                raise ConnectionError(f"Error al acceder al directorio FTP: {e}")
            
            # Filtrar archivos que contengan la cédula
            matching_files = []
            for file_path in all_files:
                filename = os.path.basename(file_path)
                
                # Validar que es un archivo válido
                if not filename or filename in ['.', '..'] or filename.endswith('/'):
                    continue
                
                # Verificar que es un PDF y contiene la cédula
                if filename.lower().endswith('.pdf') and cedula in filename:
                    matching_files.append(filename)
            
            # Ordenar por nombre para consistencia
            matching_files.sort()
            return matching_files
        
    except Exception as e:
        raise ConnectionError(f"Error durante la búsqueda FTP: {str(e)}")





# Función list_files eliminada - usar list_files_in_directory en su lugar


def rename_file(remote_subdir: str, old_name: str, new_name: str) -> bool:
    """Renombra un archivo en el servidor FTP."""
    try:
        # Construir ruta remota usando helper
        remote_dir = _build_remote_path(remote_subdir)
        src = f"{remote_dir}/{old_name}"
        dst = f"{remote_dir}/{new_name}"
        
        with ftp_connection() as ftp:
            ftp.rename(src, dst)
            return True
            
    except (ConnectionError, Exception):
        return False


def move_file(old_subdir: str, new_subdir: str, filename: str) -> Optional[str]:
    """Mueve un archivo entre subcarpetas. Devuelve la nueva ruta completa si tuvo éxito."""
    try:
        print(f"🔍 DEBUG: Intentando mover {filename} de {old_subdir} a {new_subdir}")
        
        # Construir rutas remotas usando helper
        src_dir = _build_remote_path(old_subdir)
        dst_dir = _build_remote_path(new_subdir)
        
        src = f"{src_dir}/{filename}"
        dst = f"{dst_dir}/{filename}"
        
        print(f"🔍 DEBUG: Rutas - Origen: {src}, Destino: {dst}")
        
        with ftp_connection() as ftp:
            print(f"🔍 DEBUG: Conexión FTP establecida")
            
            # Verificar que el archivo origen existe
            try:
                ftp.size(src)
                print(f"🔍 DEBUG: Archivo origen existe: {src}")
            except Exception as e:
                print(f"❌ DEBUG: Archivo origen no existe: {src} - Error: {e}")
                return None
            
            _ensure_dirs(ftp, dst_dir)
            print(f"🔍 DEBUG: Directorio destino asegurado: {dst_dir}")
            
            ftp.rename(src, dst)
            print(f"✅ DEBUG: Archivo renombrado exitosamente: {src} -> {dst}")
            return dst
            
    except Exception as e:
        print(f"❌ DEBUG: Error moviendo archivo {filename}: {e}")
        return None


def delete_file(remote_subdir: str, filename: str) -> bool:
    """Elimina un archivo del servidor FTP."""
    try:
        # Construir ruta remota usando helper
        remote_dir = _build_remote_path(remote_subdir)
        path = f"{remote_dir}/{filename}"
        
        with ftp_connection() as ftp:
            ftp.delete(path)
            return True
            
    except error_perm as e:
        if str(e).startswith('550'):
            return False
        raise
    except (ConnectionError, Exception):
        return False


# =====================================================
# FUNCIONES PARA GESTIÓN DE COMPROBANTES
# =====================================================

def list_files_in_directory(subdir: str, with_metadata: bool = False) -> List:
    """
    Lista todos los archivos en un directorio específico.
    
    Args:
        subdir: Subdirectorio a listar ('recientes' o 'anteriores')
        with_metadata: Si True, devuelve metadatos completos. Si False, solo nombres.
        
    Returns:
        List[str] o List[dict]: Lista de nombres de archivos o metadatos completos
    """
    try:
        # Si se solicitan metadatos, usar la función optimizada
        if with_metadata:
            return _get_files_with_metadata(subdir)
        
        # Comportamiento original para compatibilidad
        remote_dir = _build_remote_path(subdir)
        
        with ftp_connection() as ftp:
            try:
                all_files = ftp.nlst(remote_dir)
            except error_perm as e:
                if str(e).startswith('550'):
                    return []
                raise ConnectionError(f"Error al acceder al directorio FTP: {e}")
            
            # Filtrar solo archivos válidos
            valid_files = _filter_valid_files(all_files)
            return valid_files
            
    except Exception as e:
        print(f"Error listando archivos en {subdir}: {e}")
        return []


def upload_file_to_ftp(local_file_path: str, subdir: str, filename: str) -> bool:
    """
    Sube un archivo local al servidor FTP.
    Wrapper de la función upload_file principal.
    """
    try:
        public_url, remote_path = upload_file(local_file_path, subdir, filename)
        return remote_path is not None
    except Exception as e:
        print(f"Error subiendo archivo {filename} a {subdir}: {e}")
        return False


def delete_file_from_ftp(subdir: str, filename: str) -> bool:
    """
    Elimina un archivo del servidor FTP.
    Wrapper de la función delete_file principal.
    """
    return delete_file(subdir, filename)


def move_file_in_ftp(source_subdir: str, target_subdir: str, filename: str) -> bool:
    """
    Mueve un archivo entre subdirectorios en el servidor FTP.
    Wrapper de la función move_file principal.
    """
    try:
        print(f"🔍 DEBUG: move_file_in_ftp llamado para {filename} de {source_subdir} a {target_subdir}")
        result = move_file(source_subdir, target_subdir, filename)
        success = result is not None
        print(f"🔍 DEBUG: move_file_in_ftp resultado: {success} (result: {result})")
        return success
    except Exception as e:
        print(f"❌ DEBUG: Error en move_file_in_ftp para {filename}: {e}")
        return False


def download_file_from_ftp(subdir: str, filename: str, local_path: str) -> bool:
    """
    Descarga un archivo del servidor FTP a una ruta local.
    """
    try:
        remote_dir = _build_remote_path(subdir)
        remote_path = f"{remote_dir}/{filename}"
        
        with ftp_connection() as ftp:
            with open(local_path, 'wb') as local_file:
                ftp.retrbinary(f'RETR {remote_path}', local_file.write)
            return True
    except Exception as e:
        print(f"Error descargando archivo {filename} de {subdir}: {e}")
        return False


def _get_files_with_metadata(subdir: str, use_cache: bool = True) -> List[dict]:
    """
    Función interna para obtener metadatos de archivos con caché.
    Usada por list_files_in_directory y find_files_by_cedula cuando with_metadata=True.
    """
    cache_key = f"metadata_{subdir}"
    
    # Verificar caché si está habilitado
    if use_cache:
        with _cache_lock:
            if cache_key in _file_metadata_cache:
                cache_data = _file_metadata_cache[cache_key]
                cache_time = cache_data.get('timestamp')
                
                # Verificar si el caché sigue siendo válido
                if cache_time and datetime.now() - cache_time < timedelta(minutes=CACHE_DURATION_MINUTES):
                    print(f"📋 Usando caché para {subdir} ({len(cache_data.get('files', []))} archivos)")
                    return cache_data.get('files', [])
    
    try:
        remote_dir = _build_remote_path(subdir)
        print(f"🔍 Obteniendo metadatos reales de {subdir}...")
        
        with ftp_connection() as ftp:
            # Cambiar al directorio
            ftp.cwd(remote_dir)
            
            # Obtener lista detallada de archivos
            file_list = []
            ftp.retrlines('LIST', file_list.append)
            
            files_with_metadata = []
            
            for line in file_list:
                # Parsear línea del comando LIST
                parts = line.split()
                if len(parts) >= 9:
                    # Verificar que no sea un directorio
                    if not line.startswith('d'):
                        filename = parts[-1]  # El último elemento es el nombre del archivo
                        
                        # Filtrar solo archivos PDF válidos
                        if filename.lower().endswith('.pdf') and filename not in ['.', '..']:
                            try:
                                size = int(parts[4]) if parts[4].isdigit() else 0
                                date_str = f"{parts[5]} {parts[6]} {parts[7]}"
                                
                                files_with_metadata.append({
                                    "filename": filename,
                                    "size": size,
                                    "size_formatted": _format_file_size(size),
                                    "date": date_str,
                                    "date_iso": _parse_ftp_date_to_iso(date_str)
                                })
                            except (ValueError, IndexError) as e:
                                print(f"Error parseando archivo {filename}: {e}")
                                continue
            
            # Guardar en caché si está habilitado
            if use_cache:
                with _cache_lock:
                    _file_metadata_cache[cache_key] = {
                        'files': files_with_metadata,
                        'timestamp': datetime.now()
                    }
                    print(f"💾 Metadatos de {subdir} guardados en caché ({len(files_with_metadata)} archivos)")
            
            return files_with_metadata
            
    except Exception as e:
        error_msg = f"Error obteniendo metadatos de archivos en {subdir}: {e}"
        print(error_msg)
        
        # Si es un error de red, devolver una lista vacía en lugar de propagar el error
        if "Network is unreachable" in str(e) or "Connection refused" in str(e) or isinstance(e, ConnectionError):
            print(f"⚠️ FTP no disponible para {subdir}. Devolviendo lista vacía.")
            return []
        
        # Para otros errores, también devolver lista vacía pero registrar más detalle
        print(f"⚠️ Error inesperado en FTP para {subdir}: {type(e).__name__}: {e}")
        return []


def clear_metadata_cache(subdir: Optional[str] = None) -> None:
    """
    Limpia el caché de metadatos de archivos.
    
    Args:
        subdir: Si se especifica, solo limpia el caché de ese subdirectorio.
                Si es None, limpia todo el caché.
    """
    with _cache_lock:
        if subdir:
            cache_key = f"metadata_{subdir}"
            if cache_key in _file_metadata_cache:
                del _file_metadata_cache[cache_key]
                print(f"🗑️ Caché limpiado para {subdir}")
        else:
            _file_metadata_cache.clear()
            print("🗑️ Todo el caché de metadatos limpiado")


def _parse_ftp_date_to_iso(date_str: str) -> str:
    """
    Convierte fecha del formato FTP a ISO format.
    
    Args:
        date_str: Fecha en formato FTP (ej: "Sep 4 11:02")
        
    Returns:
        str: Fecha en formato ISO
    """
    try:
        from datetime import datetime, timedelta
        import re
        
        # Parsear la fecha del formato FTP
        # Ejemplo: "Sep 4 11:02" o "Sep 4 2025"
        parts = date_str.split()
        if len(parts) >= 3:
            month_str = parts[0]
            day = int(parts[1])
            time_or_year = parts[2]
            
            # Mapeo de meses
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            month = month_map.get(month_str, 1)
            
            # Determinar año
            current_year = datetime.now().year
            if ':' in time_or_year:
                # Es hora, usar año actual
                year = current_year
                time_parts = time_or_year.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
            else:
                # Es año
                year = int(time_or_year)
                hour = 0
                minute = 0
            
            # Crear datetime object
            file_date = datetime(year, month, day, hour, minute)
            
            # Si la fecha es en el futuro, probablemente es del año pasado
            if file_date > datetime.now():
                file_date = file_date.replace(year=year - 1)
            
            return file_date.isoformat()
            
    except Exception as e:
        print(f"Error parseando fecha {date_str}: {e}")
        # Fallback a fecha actual
        return datetime.now().isoformat()
    
    return datetime.now().isoformat()

 
