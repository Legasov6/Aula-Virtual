import customtkinter as ctk
import psycopg2
from conexion import conectar_bd

BG_COLOR = "#282828"
SIDEBAR_COLOR = "#3c3836"
ACCENT_COLOR = "#d79921"
TEXT_COLOR = "#ebdbb2"
RED_COLOR = "#cc241d"
GREEN_COLOR = "#98971a"

# ==========================================
# VENTANA MODAL: NUEVO PROFESOR
# ==========================================
class VentanaNuevoProfesor(ctk.CTkToplevel):
    def __init__(self, master, callback_actualizar):
        super().__init__(master)
        self.title("Nuevo Profesor")
        self.geometry("400x600")
        self.configure(fg_color=BG_COLOR)
        self.grab_set() 
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text="Registrar Docente", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_COLOR).pack(pady=15)

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
                    "INSERT INTO profesor (cedula, nombres, apellidos, email, telefono, fecha_nacimiento) VALUES (%s, %s, %s, %s, %s, %s)",
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
# VENTANA MODAL: EDITAR PROFESOR
# ==========================================
class VentanaEditarProfesor(ctk.CTkToplevel):
    def __init__(self, master, id_profesor, callback_actualizar):
        super().__init__(master)
        self.title("Editar Profesor")
        self.geometry("400x600")
        self.configure(fg_color=BG_COLOR)
        self.grab_set() 
        
        self.id_profesor = id_profesor
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text="Editar Docente", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_COLOR).pack(pady=15)

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
                cur.execute("SELECT cedula, nombres, apellidos, email, telefono, fecha_nacimiento FROM profesor WHERE id_profesor = %s", (self.id_profesor,))
                prof = cur.fetchone()
                if prof:
                    self.ent_cedula.insert(0, prof[0])
                    self.ent_nombres.insert(0, prof[1])
                    self.ent_apellidos.insert(0, prof[2])
                    self.ent_email.insert(0, prof[3])
                    if prof[4]: self.ent_telefono.insert(0, prof[4])
                    if prof[5]: self.ent_fecha_nac.insert(0, prof[5].strftime("%Y-%m-%d"))
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
                    "UPDATE profesor SET cedula=%s, nombres=%s, apellidos=%s, email=%s, telefono=%s, fecha_nacimiento=%s WHERE id_profesor=%s",
                    (cedula, nombres, apellidos, email, telefono, fecha_nac, self.id_profesor)
                )
                conn.commit()
                self.callback_actualizar()
                self.destroy()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                self.lbl_error.configure(text="Error: Cédula o Correo ya en uso.")
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error inesperado: {e}")
            finally:
                cur.close()
                conn.close()

# ==========================================
# VENTANA MODAL: PERFIL DOCENTE (Secciones)
# ==========================================
class VentanaPerfilProfesor(ctk.CTkToplevel):
    def __init__(self, master, id_profesor):
        super().__init__(master)
        self.id_profesor = id_profesor
        
        self.title("Perfil del Docente")
        self.geometry("600x450")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()

        self.lbl_nombre = ctk.CTkLabel(self, text="Cargando...", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT_COLOR)
        self.lbl_nombre.pack(pady=(20, 5))

        self.lbl_datos = ctk.CTkLabel(self, text="", text_color=TEXT_COLOR)
        self.lbl_datos.pack(pady=(0, 15))

        ctk.CTkLabel(self, text="Secciones Asignadas", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_COLOR).pack(pady=(10, 5))

        self.tabla_secciones = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_secciones.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_secciones.grid_columnconfigure((0,1,2), weight=1)

        self.cargar_datos()

    def cargar_datos(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                # 1. Cargar info básica
                cur.execute("SELECT cedula, nombres, apellidos, email, telefono FROM profesor WHERE id_profesor = %s", (self.id_profesor,))
                prof = cur.fetchone()
                if prof:
                    self.lbl_nombre.configure(text=f"Prof. {prof[2]}, {prof[1]}")
                    tel_str = prof[4] if prof[4] else "N/A"
                    self.lbl_datos.configure(text=f"C.I: {prof[0]}  |  Email: {prof[3]}  |  Teléfono: {tel_str}")

                # 2. Cargar secciones (Funciona porque las tablas seccion, curso y periodo ya existen)
                encabezados = ["Periodo", "Curso", "Sección"]
                for i, txt in enumerate(encabezados):
                    ctk.CTkLabel(self.tabla_secciones, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=5, sticky="w")

                cur.execute('''
                    SELECT p.codigo_periodo, c.nombre, s.identificador 
                    FROM seccion s
                    JOIN curso c ON s.id_curso = c.id_curso
                    JOIN periodo p ON s.id_periodo = p.id_periodo
                    WHERE s.id_profesor = %s
                    ORDER BY p.id_periodo DESC, c.nombre
                ''', (self.id_profesor,))
                
                secciones = cur.fetchall()

                if not secciones:
                    ctk.CTkLabel(self.tabla_secciones, text="No tiene secciones asignadas aún.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=3, pady=20)
                else:
                    for i, (periodo, curso, sec) in enumerate(secciones, start=1):
                        ctk.CTkLabel(self.tabla_secciones, text=periodo, text_color=TEXT_COLOR).grid(row=i, column=0, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(self.tabla_secciones, text=curso, text_color=TEXT_COLOR).grid(row=i, column=1, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(self.tabla_secciones, text=sec, text_color=TEXT_COLOR).grid(row=i, column=2, padx=5, pady=5, sticky="w")

            except Exception as e:
                ctk.CTkLabel(self.tabla_secciones, text=f"Error: {e}", text_color=RED_COLOR).grid(row=1, column=0)
            finally:
                cur.close()
                conn.close()

# ==========================================
# PANEL PRINCIPAL: VISTA ADMIN (Profesores)
# ==========================================
class VistaAdminProfesores(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_COLOR)
        
        self.titulo = ctk.CTkLabel(self, text="Directorio Docente", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.titulo.pack(pady=(20, 10))

        frame_controles = ctk.CTkFrame(self, fg_color="transparent")
        frame_controles.pack(fill="x", padx=20, pady=10)

        self.btn_listar = ctk.CTkButton(frame_controles, text="Recargar", width=90, fg_color=ACCENT_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.cargar_profesores)
        self.btn_listar.pack(side="left", padx=5)

        self.btn_nuevo = ctk.CTkButton(frame_controles, text="+ Nuevo Docente", width=120, fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, text_color=TEXT_COLOR, command=self.abrir_modal_nuevo)
        self.btn_nuevo.pack(side="left", padx=5)

        ctk.CTkLabel(frame_controles, text="Buscar:", text_color=TEXT_COLOR).pack(side="left", padx=(20, 2))
        self.ent_busqueda = ctk.CTkEntry(frame_controles, placeholder_text="Cédula o Apellido...", width=150, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_busqueda.pack(side="left", padx=5)
        self.ent_busqueda.bind("<Return>", lambda event: self.cargar_profesores())

        self.tabla_frame = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.tabla_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        self.tabla_frame.grid_columnconfigure(5, weight=0)

    def abrir_modal_nuevo(self):
        VentanaNuevoProfesor(self, self.cargar_profesores)

    def cargar_profesores(self, *args):
        termino_busqueda = self.ent_busqueda.get().strip()

        for widget in self.tabla_frame.winfo_children():
            widget.destroy()

        encabezados = ["Cédula", "Apellidos", "Nombres", "Email", "Teléfono", "Acciones"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_frame, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = "SELECT id_profesor, cedula, nombres, apellidos, email, telefono FROM profesor"
                params = []

                if termino_busqueda != "":
                    query += " WHERE cedula ILIKE %s OR apellidos ILIKE %s"
                    params.extend([f"%{termino_busqueda}%", f"%{termino_busqueda}%"])

                query += " ORDER BY apellidos, nombres"
                
                cur.execute(query, tuple(params))
                profesores = cur.fetchall()

                if not profesores:
                    ctk.CTkLabel(self.tabla_frame, text="No se encontraron profesores.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=6, pady=20)

                for fila_idx, prof in enumerate(profesores, start=1):
                    id_prof, cedula, nombres, apellidos, email, telefono = prof

                    tel_str = telefono if telefono else "N/A"

                    ctk.CTkLabel(self.tabla_frame, text=cedula, text_color=TEXT_COLOR).grid(row=fila_idx, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=apellidos, text_color=TEXT_COLOR).grid(row=fila_idx, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=nombres, text_color=TEXT_COLOR).grid(row=fila_idx, column=2, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=email, text_color=TEXT_COLOR).grid(row=fila_idx, column=3, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_frame, text=tel_str, text_color=TEXT_COLOR).grid(row=fila_idx, column=4, padx=5, pady=5, sticky="w")

                    frame_acciones = ctk.CTkFrame(self.tabla_frame, fg_color="transparent")
                    frame_acciones.grid(row=fila_idx, column=5, padx=5, pady=5, sticky="e")

                    btn_ver = ctk.CTkButton(frame_acciones, text="Ver", width=50, fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=lambda e=id_prof: VentanaPerfilProfesor(self, e))
                    btn_ver.pack(side="left", padx=2)

                    btn_editar = ctk.CTkButton(frame_acciones, text="Editar", width=50, fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, text_color=TEXT_COLOR, command=lambda e=id_prof: VentanaEditarProfesor(self, e, self.cargar_profesores))
                    btn_editar.pack(side="left", padx=2)

                    btn_borrar = ctk.CTkButton(frame_acciones, text="X", width=30, fg_color=RED_COLOR, text_color=TEXT_COLOR, command=lambda e=id_prof: self.borrar_profesor(e))
                    btn_borrar.pack(side="left", padx=2)

            except Exception as e:
                print("Error cargando profesores:", e)
            finally:
                cur.close()
                conn.close()

    def borrar_profesor(self, id_profesor):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("DELETE FROM profesor WHERE id_profesor = %s", (id_profesor,))
                conn.commit()
                self.cargar_profesores()
            except Exception as e:
                conn.rollback()
                print(f"Error borrando profesor: {e}")
            finally:
                cur.close()
                conn.close()