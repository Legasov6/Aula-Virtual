import customtkinter as ctk
import psycopg2
from conexion import conectar_bd

# Paleta de colores
BG_COLOR = "#282828"
SIDEBAR_COLOR = "#3c3836"
ACCENT_COLOR = "#d79921"
TEXT_COLOR = "#ebdbb2"
RED_COLOR = "#cc241d"
GREEN_COLOR = "#98971a"

# ==========================================
# VENTANA MODAL: NUEVO ESTUDIANTE
# ==========================================
class VentanaNuevoEstudiante(ctk.CTkToplevel):
    def __init__(self, master, callback_actualizar):
        super().__init__(master)
        self.title("Nuevo Estudiante")
        self.geometry("400x600")
        self.configure(fg_color=BG_COLOR)
        self.grab_set() 
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text="Registrar Estudiante", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_COLOR).pack(pady=15)

        self.ent_cedula = ctk.CTkEntry(self, placeholder_text="Cédula", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_cedula.pack(pady=10)

        self.ent_nombres = ctk.CTkEntry(self, placeholder_text="Nombres", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_nombres.pack(pady=10)

        self.ent_apellidos = ctk.CTkEntry(self, placeholder_text="Apellidos", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_apellidos.pack(pady=10)

        self.ent_email = ctk.CTkEntry(self, placeholder_text="Correo Electrónico", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_email.pack(pady=10)

        self.ent_telefono = ctk.CTkEntry(self, placeholder_text="Teléfono", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_telefono.pack(pady=10)

        self.ent_fecha_nac = ctk.CTkEntry(self, placeholder_text="Fecha Nacimiento (YYYY-MM-DD)", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_fecha_nac.pack(pady=10)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=RED_COLOR)
        self.lbl_error.pack(pady=5)

        btn_guardar = ctk.CTkButton(self, text="Guardar", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.guardar_bd)
        btn_guardar.pack(pady=10)

    def guardar_bd(self):
        cedula = self.ent_cedula.get().strip()
        nombres = self.ent_nombres.get().strip()
        apellidos = self.ent_apellidos.get().strip()
        email = self.ent_email.get().strip()
        telefono = self.ent_telefono.get().strip()
        fecha_nac = self.ent_fecha_nac.get().strip()

        if not all([cedula, nombres, apellidos, email, telefono, fecha_nac]):
            self.lbl_error.configure(text="Todos los campos son obligatorios.")
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute(
                    "INSERT INTO estudiante (cedula, nombres, apellidos, email, telefono, fecha_nacimiento) VALUES (%s, %s, %s, %s, %s, %s)",
                    (cedula, nombres, apellidos, email, telefono, fecha_nac)
                )
                conn.commit()
                self.callback_actualizar()
                self.destroy()
            except psycopg2.errors.UniqueViolation as e:
                conn.rollback()
                if "cedula" in str(e):
                    self.lbl_error.configure(text="Error: Esta cédula ya está registrada.")
                elif "email" in str(e):
                    self.lbl_error.configure(text="Error: Este correo ya está en uso.")
            except psycopg2.errors.DatetimeFieldOverflow:
                conn.rollback()
                self.lbl_error.configure(text="Error: Formato de fecha inválido. Usa YYYY-MM-DD.")
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error inesperado: {e}")
            finally:
                cur.close()
                conn.close()

# ==========================================
# VENTANA MODAL: EDITAR ESTUDIANTE
# ==========================================
class VentanaEditarEstudiante(ctk.CTkToplevel):
    def __init__(self, master, id_estudiante, callback_actualizar):
        super().__init__(master)
        self.title("Editar Estudiante")
        self.geometry("400x600")
        self.configure(fg_color=BG_COLOR)
        self.grab_set() 
        
        self.id_estudiante = id_estudiante
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text="Editar Estudiante", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_COLOR).pack(pady=15)

        self.ent_cedula = ctk.CTkEntry(self, placeholder_text="Cédula", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_cedula.pack(pady=10)

        self.ent_nombres = ctk.CTkEntry(self, placeholder_text="Nombres", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_nombres.pack(pady=10)

        self.ent_apellidos = ctk.CTkEntry(self, placeholder_text="Apellidos", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_apellidos.pack(pady=10)

        self.ent_email = ctk.CTkEntry(self, placeholder_text="Correo Electrónico", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_email.pack(pady=10)

        self.ent_telefono = ctk.CTkEntry(self, placeholder_text="Teléfono", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_telefono.pack(pady=10)

        self.ent_fecha_nac = ctk.CTkEntry(self, placeholder_text="Fecha Nacimiento (YYYY-MM-DD)", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_fecha_nac.pack(pady=10)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=RED_COLOR)
        self.lbl_error.pack(pady=5)

        btn_guardar = ctk.CTkButton(self, text="Actualizar Datos", fg_color=ACCENT_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.actualizar_bd)
        btn_guardar.pack(pady=10)

        self.cargar_datos_actuales()

    def cargar_datos_actuales(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT cedula, nombres, apellidos, email, telefono, fecha_nacimiento FROM estudiante WHERE id_estudiante = %s", (self.id_estudiante,))
                est = cur.fetchone()
                if est:
                    self.ent_cedula.insert(0, est[0])
                    self.ent_nombres.insert(0, est[1])
                    self.ent_apellidos.insert(0, est[2])
                    self.ent_email.insert(0, est[3])
                    if est[4]: self.ent_telefono.insert(0, est[4])
                    if est[5]: self.ent_fecha_nac.insert(0, est[5].strftime("%Y-%m-%d"))
            except Exception as e:
                self.lbl_error.configure(text=f"Error al cargar datos: {e}")
            finally:
                cur.close()
                conn.close()

    def actualizar_bd(self):
        cedula = self.ent_cedula.get().strip()
        nombres = self.ent_nombres.get().strip()
        apellidos = self.ent_apellidos.get().strip()
        email = self.ent_email.get().strip()
        telefono = self.ent_telefono.get().strip()
        fecha_nac = self.ent_fecha_nac.get().strip()

        if not all([cedula, nombres, apellidos, email, telefono, fecha_nac]):
            self.lbl_error.configure(text="Todos los campos son obligatorios.")
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute(
                    "UPDATE estudiante SET cedula=%s, nombres=%s, apellidos=%s, email=%s, telefono=%s, fecha_nacimiento=%s WHERE id_estudiante=%s",
                    (cedula, nombres, apellidos, email, telefono, fecha_nac, self.id_estudiante)
                )
                conn.commit()
                self.callback_actualizar()
                self.destroy()
            except psycopg2.errors.UniqueViolation as e:
                conn.rollback()
                self.lbl_error.configure(text="Error: Cédula o Correo ya asignado a otra persona.")
            except psycopg2.errors.DatetimeFieldOverflow:
                conn.rollback()
                self.lbl_error.configure(text="Error: Formato de fecha inválido. Usa YYYY-MM-DD.")
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error inesperado: {e}")
            finally:
                cur.close()
                conn.close()

# ==========================================
# VENTANA MODAL: RECARGAR SALDO
# ==========================================
class VentanaRecargaSaldo(ctk.CTkToplevel):
    def __init__(self, master, id_estudiante, callback_kardex, callback_tabla):
        super().__init__(master)
        self.title("Recarga de Billetera")
        self.geometry("300x200")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()

        self.id_estudiante = id_estudiante
        self.callback_kardex = callback_kardex
        self.callback_tabla = callback_tabla

        ctk.CTkLabel(self, text="Monto a recargar ($):", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_COLOR).pack(pady=(20, 10))
        
        self.ent_monto = ctk.CTkEntry(self, width=150, justify="center", fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_monto.pack(pady=5)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=RED_COLOR)
        self.lbl_error.pack(pady=2)

        btn_procesar = ctk.CTkButton(self, text="Procesar Pago", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.procesar_pago)
        btn_procesar.pack(pady=10)

    def procesar_pago(self):
        monto_str = self.ent_monto.get().strip()
        try:
            monto = float(monto_str)
            if monto <= 0:
                self.lbl_error.configure(text="El monto debe ser mayor a 0.")
                return
        except ValueError:
            self.lbl_error.configure(text="Ingresa un valor numérico válido.")
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                # 1. Actualiza el saldo en la billetera
                cur.execute("UPDATE estudiante SET saldo = saldo + %s WHERE id_estudiante = %s", (monto, self.id_estudiante))
                
                # 2. Guarda el recibo en la tabla pago
                cur.execute("INSERT INTO pago (monto, concepto_pago, id_estudiante) VALUES (%s, %s, %s)", 
                            (monto, "Recarga de saldo en caja", self.id_estudiante))
                
                conn.commit()
                
                self.callback_kardex() 
                self.callback_tabla()  
                self.destroy()
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error: {e}")
            finally:
                cur.close()
                conn.close()

# ==========================================
# VENTANA MODAL: KÁRDEX / EXPEDIENTE
# ==========================================
class VentanaKardex(ctk.CTkToplevel):
    def __init__(self, master, id_estudiante, callback_actualizar):
        super().__init__(master)
        self.id_estudiante = id_estudiante
        self.callback_actualizar = callback_actualizar 
        
        self.title("Expediente del Estudiante")
        self.geometry("750x650") 
        self.configure(fg_color=BG_COLOR)
        self.grab_set()

        # Cabecera
        frame_cabecera = ctk.CTkFrame(self, fg_color="transparent")
        frame_cabecera.pack(fill="x", padx=20, pady=(20, 5))

        self.lbl_nombre = ctk.CTkLabel(frame_cabecera, text="Cargando...", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT_COLOR)
        self.lbl_nombre.pack(side="left")

        self.btn_recargar = ctk.CTkButton(frame_cabecera, text="+ Recargar Saldo", width=120, fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.abrir_recarga)
        self.btn_recargar.pack(side="right")

        self.lbl_datos = ctk.CTkLabel(self, text="", text_color=TEXT_COLOR)
        self.lbl_datos.pack(pady=(0, 10))

        # --- SECCIÓN 1: CARRERAS INSCRITAS ---
        ctk.CTkLabel(self, text="Carreras Inscritas", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_COLOR).pack(pady=(5, 5))

        self.frame_carreras = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR, height=100)
        self.frame_carreras.pack(padx=20, pady=5, fill="x")
        self.frame_carreras.grid_columnconfigure((0, 1, 2), weight=1) # 3 columnas ahora

        frame_nueva_carrera = ctk.CTkFrame(self, fg_color="transparent")
        frame_nueva_carrera.pack(pady=5)

        self.combo_carreras = ctk.CTkOptionMenu(frame_nueva_carrera, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, button_hover_color="#b57614")
        self.combo_carreras.pack(side="left", padx=10)

        btn_inscribir = ctk.CTkButton(frame_nueva_carrera, text="+ Inscribir", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.inscribir_carrera)
        btn_inscribir.pack(side="left")

        self.lbl_mensaje = ctk.CTkLabel(self, text="", text_color=TEXT_COLOR)
        self.lbl_mensaje.pack(pady=5)

        # --- SECCIÓN 2: KÁRDEX DE NOTAS ---
        ctk.CTkLabel(self, text="Kárdex de Notas (Historial Académico)", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_COLOR).pack(pady=(10, 5))

        self.tabla_notas = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR, height=200)
        self.tabla_notas.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_notas.grid_columnconfigure((0,1,2,3), weight=1)

        self.mapa_carreras = {}
        self.cargar_datos()

    def abrir_recarga(self):
        VentanaRecargaSaldo(self, self.id_estudiante, self.cargar_datos, self.callback_actualizar)

    def cargar_datos(self):
        for widget in self.frame_carreras.winfo_children():
            widget.destroy()
        for widget in self.tabla_notas.winfo_children():
            widget.destroy()

        # Encabezados en Carreras
        ctk.CTkLabel(self.frame_carreras, text="CARRERA", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkLabel(self.frame_carreras, text="ESTADO", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ctk.CTkLabel(self.frame_carreras, text="FECHA INGRESO", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=2, sticky="w", padx=5, pady=5)

        # Encabezados en Notas
        encabezados_notas = ["Periodo", "Materia", "Nota Acumulada", "Estado"]
        for i, texto in enumerate(encabezados_notas):
            ctk.CTkLabel(self.tabla_notas, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                # 1. Cargar Datos Básicos del Estudiante
                cur.execute("SELECT cedula, nombres, apellidos, email, saldo, fecha_nacimiento, telefono FROM estudiante WHERE id_estudiante = %s", (self.id_estudiante,))
                est = cur.fetchone()
                
                if est:
                    self.lbl_nombre.configure(text=f"Expediente: {est[2]}, {est[1]}")
                    fecha_str = est[5].strftime("%Y-%m-%d") if est[5] else "N/A"
                    tel_str = est[6] if est[6] else "N/A"
                    texto_datos = f"C.I: {est[0]}  |  Nacimiento: {fecha_str}  |  Teléfono: {tel_str}\nEmail: {est[3]}  |  Saldo Disponible: ${est[4]:.2f}"
                    self.lbl_datos.configure(text=texto_datos)

                # 2. Cargar Carreras (Agregando fecha_inscripcion)
                cur.execute('''
                    SELECT c.nombre, ec.estado, ec.fecha_inscripcion
                    FROM expediente_carrera ec
                    JOIN carrera c ON ec.id_carrera = c.id_carrera
                    WHERE ec.id_estudiante = %s
                ''', (self.id_estudiante,))
                carreras_inscritas = cur.fetchall()

                for i, (nombre_carrera, estado, fecha) in enumerate(carreras_inscritas, start=1):
                    fecha_ingreso = fecha.strftime("%Y-%m-%d") if fecha else "N/A"
                    ctk.CTkLabel(self.frame_carreras, text=nombre_carrera, text_color=TEXT_COLOR).grid(row=i, column=0, sticky="w", padx=5, pady=2)
                    ctk.CTkLabel(self.frame_carreras, text=estado, text_color=TEXT_COLOR).grid(row=i, column=1, sticky="w", padx=5, pady=2)
                    ctk.CTkLabel(self.frame_carreras, text=fecha_ingreso, text_color=TEXT_COLOR).grid(row=i, column=2, sticky="w", padx=5, pady=2)

                cur.execute('''
                    SELECT id_carrera, nombre FROM carrera
                    WHERE id_carrera NOT IN (
                        SELECT id_carrera FROM expediente_carrera WHERE id_estudiante = %s
                    )
                ''', (self.id_estudiante,))
                carreras_disponibles = cur.fetchall()

                if carreras_disponibles:
                    nombres_carreras = []
                    self.mapa_carreras = {}
                    for id_c, nombre in carreras_disponibles:
                        nombres_carreras.append(nombre)
                        self.mapa_carreras[nombre] = id_c 
                    
                    self.combo_carreras.configure(values=nombres_carreras, state="normal")
                    self.combo_carreras.set(nombres_carreras[0])
                else:
                    self.combo_carreras.configure(values=["Sin opciones / Ya cursando todo"], state="disabled")
                    self.combo_carreras.set("Sin opciones / Ya cursando todo")
                    self.mapa_carreras = {}

                # 3. Cargar Kárdex de Notas
                query_kardex = '''
                    SELECT pe.codigo_periodo, cu.nombre,
                           COALESCE(SUM(cal.nota_numerica * (ev.ponderacion / 100.0)), 0) as nota_acumulada,
                           COALESCE(SUM(ev.ponderacion), 0) as porcentaje_evaluado
                    FROM inscripcion i
                    JOIN seccion s ON i.id_seccion = s.id_seccion
                    JOIN periodo pe ON s.id_periodo = pe.id_periodo
                    JOIN curso cu ON s.id_curso = cu.id_curso
                    LEFT JOIN evaluacion ev ON s.id_seccion = ev.id_seccion
                    LEFT JOIN calificacion cal ON ev.id_evaluacion = cal.id_evaluacion AND cal.id_estudiante = i.id_estudiante
                    WHERE i.id_estudiante = %s
                    GROUP BY pe.id_periodo, pe.codigo_periodo, cu.nombre
                    ORDER BY pe.id_periodo DESC, cu.nombre
                '''
                cur.execute(query_kardex, (self.id_estudiante,))
                historial = cur.fetchall()

                if not historial:
                    ctk.CTkLabel(self.tabla_notas, text="El estudiante no tiene historial de notas.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=4, pady=20)
                else:
                    for fila_idx, (periodo, curso, nota_acumulada, porcentaje_evaluado) in enumerate(historial, start=1):
                        nota_acumulada = float(nota_acumulada)
                        porcentaje_evaluado = float(porcentaje_evaluado)

                        estado_texto = "Cursando / Sin notas"
                        color_estado = TEXT_COLOR

                        if porcentaje_evaluado == 100.0:
                            if nota_acumulada >= 5.0:
                                estado_texto = "Aprobado"
                                color_estado = GREEN_COLOR
                            else:
                                estado_texto = "Reprobado"
                                color_estado = RED_COLOR
                        elif porcentaje_evaluado > 0.0:
                            estado_texto = f"En progreso ({porcentaje_evaluado}%)"

                        ctk.CTkLabel(self.tabla_notas, text=periodo, text_color=TEXT_COLOR).grid(row=fila_idx, column=0, padx=5, pady=2, sticky="w")
                        ctk.CTkLabel(self.tabla_notas, text=curso, text_color=TEXT_COLOR).grid(row=fila_idx, column=1, padx=5, pady=2, sticky="w")
                        ctk.CTkLabel(self.tabla_notas, text=f"{nota_acumulada:.2f} / 10", text_color=TEXT_COLOR, font=ctk.CTkFont(weight="bold")).grid(row=fila_idx, column=2, padx=5, pady=2, sticky="w")
                        ctk.CTkLabel(self.tabla_notas, text=estado_texto, text_color=color_estado, font=ctk.CTkFont(weight="bold")).grid(row=fila_idx, column=3, padx=5, pady=2, sticky="w")

            except Exception as e:
                self.lbl_mensaje.configure(text=f"Error cargando expediente: {e}", text_color=RED_COLOR)
                print("Error cargando expediente:", e)
            finally:
                cur.close()
                conn.close()

    def inscribir_carrera(self):
        carrera_seleccionada = self.combo_carreras.get()
        if carrera_seleccionada not in self.mapa_carreras:
            return

        id_carrera = self.mapa_carreras[carrera_seleccionada]
        
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute(
                    "INSERT INTO expediente_carrera (id_estudiante, id_carrera, estado) VALUES (%s, %s, 'Activo')",
                    (self.id_estudiante, id_carrera)
                )
                conn.commit()
                self.lbl_mensaje.configure(text=f"Inscrito en {carrera_seleccionada} exitosamente.", text_color=GREEN_COLOR)
                self.cargar_datos() 
                self.callback_actualizar()
            except Exception as e:
                conn.rollback()
                self.lbl_mensaje.configure(text=f"Error al inscribir: {e}", text_color=RED_COLOR)
            finally:
                cur.close()
                conn.close()

# ==========================================
# PANEL PRINCIPAL: VISTA ADMIN (Estudiantes)
# ==========================================
class VistaAdmin(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_COLOR)
        
        self.titulo = ctk.CTkLabel(self, text="Gestión de Estudiantes", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.titulo.pack(pady=(20, 10))

        frame_controles = ctk.CTkFrame(self, fg_color="transparent")
        frame_controles.pack(fill="x", padx=20, pady=10)

        self.btn_listar = ctk.CTkButton(frame_controles, text="Recargar", width=90, fg_color=ACCENT_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.cargar_estudiantes)
        self.btn_listar.pack(side="left", padx=5)

        self.btn_nuevo = ctk.CTkButton(frame_controles, text="+ Nuevo", width=90, fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, text_color=TEXT_COLOR, command=self.abrir_modal_nuevo)
        self.btn_nuevo.pack(side="left", padx=5)

        ctk.CTkLabel(frame_controles, text="Carrera:", text_color=TEXT_COLOR).pack(side="left", padx=(15, 2))
        self.combo_filtro = ctk.CTkOptionMenu(frame_controles, width=160, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, command=self.cargar_estudiantes)
        self.combo_filtro.pack(side="left", padx=5)
        self.cargar_opciones_filtro()

        ctk.CTkLabel(frame_controles, text="Cédula:", text_color=TEXT_COLOR).pack(side="left", padx=(15, 2))
        self.ent_busqueda = ctk.CTkEntry(frame_controles, placeholder_text="Ej: 3012...", width=130, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_busqueda.pack(side="left", padx=5)
        self.ent_busqueda.bind("<Return>", lambda event: self.cargar_estudiantes())

        self.btn_buscar = ctk.CTkButton(frame_controles, text="Buscar", width=70, fg_color=ACCENT_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.cargar_estudiantes)
        self.btn_buscar.pack(side="left", padx=5)

        self.tabla_frame = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.tabla_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        self.tabla_frame.grid_columnconfigure(5, weight=0)

    def cargar_opciones_filtro(self):
        conn, cur = conectar_bd()
        opciones = ["Todas"]
        if conn:
            try:
                cur.execute("SELECT nombre FROM carrera ORDER BY nombre;")
                carreras = cur.fetchall()
                opciones.extend([c[0] for c in carreras])
            except Exception as e:
                print("Error cargando filtro:", e)
            finally:
                cur.close()
                conn.close()
        self.combo_filtro.configure(values=opciones)
        self.combo_filtro.set("Todas")

    def abrir_modal_nuevo(self):
        VentanaNuevoEstudiante(self, self.cargar_estudiantes)

    def cargar_estudiantes(self, *args):
        filtro_carrera = self.combo_filtro.get()
        termino_busqueda = self.ent_busqueda.get().strip()

        for widget in self.tabla_frame.winfo_children():
            widget.destroy()

        encabezados = ["Cédula", "Apellidos", "Nombres", "Carrera(s)", "Saldo", "Acciones"]
        for i, texto in enumerate(encabezados):
            lbl = ctk.CTkLabel(self.tabla_frame, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR)
            lbl.grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT e.id_estudiante, e.cedula, e.nombres, e.apellidos, e.saldo,
                           COALESCE(STRING_AGG(c.nombre, ', '), 'Sin carrera') as carreras
                    FROM estudiante e
                    LEFT JOIN expediente_carrera ec ON e.id_estudiante = ec.id_estudiante
                    LEFT JOIN carrera c ON ec.id_carrera = c.id_carrera
                '''
                
                condiciones = []
                params = []

                if filtro_carrera != "Todas":
                    condiciones.append('''
                        e.id_estudiante IN (
                            SELECT ec2.id_estudiante 
                            FROM expediente_carrera ec2 
                            JOIN carrera c2 ON ec2.id_carrera = c2.id_carrera 
                            WHERE c2.nombre = %s
                        )
                    ''')
                    params.append(filtro_carrera)
                
                if termino_busqueda != "":
                    condiciones.append("e.cedula ILIKE %s")
                    params.append(f"%{termino_busqueda}%")

                if condiciones:
                    query += " WHERE " + " AND ".join(condiciones)

                query += " GROUP BY e.id_estudiante, e.cedula, e.nombres, e.apellidos, e.saldo ORDER BY e.apellidos, e.nombres;"
                
                cur.execute(query, tuple(params))
                estudiantes = cur.fetchall()

                if not estudiantes:
                    ctk.CTkLabel(self.tabla_frame, text="No se encontraron estudiantes.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=6, pady=20)

                for fila_idx, est in enumerate(estudiantes, start=1):
                    id_est, cedula, nombres, apellidos, saldo, carreras_str = est

                    ctk.CTkLabel(self.tabla_frame, text=cedula, text_color=TEXT_COLOR).grid(row=fila_idx, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=apellidos, text_color=TEXT_COLOR).grid(row=fila_idx, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=nombres, text_color=TEXT_COLOR).grid(row=fila_idx, column=2, padx=5, pady=5, sticky="w")
                    
                    lbl_carrera = ctk.CTkLabel(self.tabla_frame, text=carreras_str, text_color=TEXT_COLOR, width=150, anchor="w")
                    lbl_carrera.grid(row=fila_idx, column=3, padx=5, pady=5, sticky="w")

                    ctk.CTkLabel(self.tabla_frame, text=f"${saldo:.2f}", text_color=TEXT_COLOR).grid(row=fila_idx, column=4, padx=5, pady=5, sticky="w")

                    frame_acciones = ctk.CTkFrame(self.tabla_frame, fg_color="transparent")
                    frame_acciones.grid(row=fila_idx, column=5, padx=5, pady=5, sticky="e")

                    btn_ver = ctk.CTkButton(frame_acciones, text="Ver", width=50, fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=lambda e=id_est: self.ver_expediente(e))
                    btn_ver.pack(side="left", padx=2)

                    btn_editar = ctk.CTkButton(frame_acciones, text="Editar", width=50, fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, text_color=TEXT_COLOR, command=lambda e=id_est: self.editar_estudiante(e))
                    btn_editar.pack(side="left", padx=2)

                    btn_borrar = ctk.CTkButton(frame_acciones, text="X", width=30, fg_color=RED_COLOR, text_color=TEXT_COLOR, command=lambda e=id_est: self.borrar_estudiante(e))
                    btn_borrar.pack(side="left", padx=2)

            except Exception as e:
                print("Error cargando estudiantes:", e)
            finally:
                cur.close()
                conn.close()

    def ver_expediente(self, id_estudiante):
        VentanaKardex(self, id_estudiante, self.cargar_estudiantes)

    def editar_estudiante(self, id_estudiante):
        VentanaEditarEstudiante(self, id_estudiante, self.cargar_estudiantes)

    def borrar_estudiante(self, id_estudiante):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("DELETE FROM estudiante WHERE id_estudiante = %s", (id_estudiante,))
                conn.commit()
                self.cargar_estudiantes()
            except Exception as e:
                conn.rollback()
                print(f"Error al intentar borrar el estudiante: {e}")
            finally:
                cur.close()
                conn.close()