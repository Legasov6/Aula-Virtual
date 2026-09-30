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
# MODAL: AGREGAR MATERIA AL PENSUM
# ==========================================
class VentanaAgregarPensum(ctk.CTkToplevel):
    def __init__(self, master, id_carrera, nombre_carrera, callback_actualizar):
        super().__init__(master)
        self.title("Añadir al Pensum")
        self.geometry("400x350")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()

        self.id_carrera = id_carrera
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text=f"Agregar a: {nombre_carrera}", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_COLOR).pack(pady=15)

        self.combo_curso = ctk.CTkOptionMenu(self, width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR)
        self.combo_curso.pack(pady=10)

        self.ent_semestre = ctk.CTkEntry(self, placeholder_text="Semestre Sugerido (Ej: 1, 2, 3...)", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_semestre.pack(pady=10)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=RED_COLOR)
        self.lbl_error.pack(pady=5)

        btn_guardar = ctk.CTkButton(self, text="Guardar en Pensum", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.guardar_bd)
        btn_guardar.pack(pady=15)

        self.mapa_cursos = {}
        self.cargar_cursos_disponibles()

    def cargar_cursos_disponibles(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                # Buscar cursos que aún NO están en el pensum de esta carrera
                cur.execute('''
                    SELECT id_curso, codigo, nombre FROM curso 
                    WHERE id_curso NOT IN (SELECT id_curso FROM pensum WHERE id_carrera = %s)
                    ORDER BY nombre
                ''', (self.id_carrera,))
                cursos = cur.fetchall()

                if cursos:
                    opciones = []
                    for id_c, cod, nom in cursos:
                        texto = f"{cod} - {nom}" if cod else nom
                        opciones.append(texto)
                        self.mapa_cursos[texto] = id_c
                    self.combo_curso.configure(values=opciones)
                    self.combo_curso.set(opciones[0])
                else:
                    self.combo_curso.configure(values=["No hay cursos disponibles"])
                    self.combo_curso.set("No hay cursos disponibles")
            except Exception as e:
                self.lbl_error.configure(text=f"Error: {e}")
            finally:
                cur.close()
                conn.close()

    def guardar_bd(self):
        seleccion = self.combo_curso.get()
        semestre_str = self.ent_semestre.get().strip()

        if seleccion not in self.mapa_cursos or not semestre_str:
            self.lbl_error.configure(text="Selecciona un curso y escribe el semestre.")
            return

        try:
            semestre = int(semestre_str)
            if semestre <= 0: raise ValueError
        except ValueError:
            self.lbl_error.configure(text="El semestre debe ser un número entero positivo.")
            return

        id_curso = self.mapa_cursos[seleccion]

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("INSERT INTO pensum (id_carrera, id_curso, semestre_sugerido) VALUES (%s, %s, %s)", (self.id_carrera, id_curso, semestre))
                conn.commit()
                self.callback_actualizar()
                self.destroy()
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error al guardar: {e}")
            finally:
                cur.close()
                conn.close()

# ==========================================
# MODAL: EDITAR PERIODO
# ==========================================
class VentanaEditarPeriodo(ctk.CTkToplevel):
    def __init__(self, master, id_periodo, callback_actualizar):
        super().__init__(master)
        self.title("Editar Periodo")
        self.geometry("400x350")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()

        self.id_periodo = id_periodo
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text="Editar Periodo Académico", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_COLOR).pack(pady=15)

        self.ent_cod_periodo = ctk.CTkEntry(self, placeholder_text="Código (Ej: 2026-I)", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_cod_periodo.pack(pady=10)

        self.ent_inicio = ctk.CTkEntry(self, placeholder_text="Inicio (YYYY-MM-DD)", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_inicio.pack(pady=10)

        self.ent_fin = ctk.CTkEntry(self, placeholder_text="Fin (YYYY-MM-DD)", width=300, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_fin.pack(pady=10)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=RED_COLOR)
        self.lbl_error.pack(pady=5)

        btn_guardar = ctk.CTkButton(self, text="Actualizar", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.actualizar_bd)
        btn_guardar.pack(pady=15)

        self.cargar_datos()

    def cargar_datos(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT codigo_periodo, fecha_inicio, fecha_fin FROM periodo WHERE id_periodo = %s", (self.id_periodo,))
                per = cur.fetchone()
                if per:
                    self.ent_cod_periodo.insert(0, per[0])
                    self.ent_inicio.insert(0, str(per[1]))
                    self.ent_fin.insert(0, str(per[2]))
            except Exception as e:
                self.lbl_error.configure(text=f"Error cargando datos: {e}")
            finally:
                cur.close()
                conn.close()

    def actualizar_bd(self):
        codigo = self.ent_cod_periodo.get().strip()
        inicio = self.ent_inicio.get().strip()
        fin = self.ent_fin.get().strip()

        if not all([codigo, inicio, fin]):
            self.lbl_error.configure(text="Todos los campos son obligatorios.")
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute(
                    "UPDATE periodo SET codigo_periodo=%s, fecha_inicio=%s, fecha_fin=%s WHERE id_periodo=%s",
                    (codigo, inicio, fin, self.id_periodo)
                )
                conn.commit()
                self.callback_actualizar()
                self.destroy()
            except psycopg2.errors.CheckViolation:
                conn.rollback()
                self.lbl_error.configure(text="Error: La Fecha de Fin debe ser mayor a la de Inicio.")
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                self.lbl_error.configure(text="Error: Este código de periodo ya está en uso.")
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
# PANEL PRINCIPAL: GESTIÓN INSTITUCIONAL
# ==========================================
class VistaAdminInstitucion(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_COLOR)
        
        self.titulo = ctk.CTkLabel(self, text="Gestión Institucional", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.titulo.pack(pady=(20, 10))

        self.tabview = ctk.CTkTabview(self, fg_color=SIDEBAR_COLOR, segmented_button_selected_color=ACCENT_COLOR, segmented_button_selected_hover_color="#b57614")
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        self.tab_carreras = self.tabview.add("Carreras")
        self.tab_periodos = self.tabview.add("Periodos Académicos")
        self.tab_pensum = self.tabview.add("Pensum por Carrera")

        self.construir_pestaña_carreras()
        self.construir_pestaña_periodos()
        self.construir_pestaña_pensum()

    # --- LÓGICA DE CARRERAS ---
    def construir_pestaña_carreras(self):
        frame_form = ctk.CTkFrame(self.tab_carreras, fg_color="transparent")
        frame_form.pack(fill="x", pady=10)

        self.ent_nom_carrera = ctk.CTkEntry(frame_form, placeholder_text="Nombre de la Carrera (Ej: Ingeniería Informática)", width=350, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.ent_nom_carrera.pack(side="left", padx=5)

        btn_crear_carrera = ctk.CTkButton(frame_form, text="Crear Carrera", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.crear_carrera)
        btn_crear_carrera.pack(side="left", padx=10)

        self.lbl_msj_carrera = ctk.CTkLabel(frame_form, text="", text_color=RED_COLOR)
        self.lbl_msj_carrera.pack(side="left", padx=10)

        self.tabla_carreras = ctk.CTkScrollableFrame(self.tab_carreras, fg_color=BG_COLOR)
        self.tabla_carreras.pack(fill="both", expand=True, pady=10)
        self.tabla_carreras.grid_columnconfigure(0, weight=1)
        self.tabla_carreras.grid_columnconfigure(1, weight=0)

        self.cargar_carreras()

    def crear_carrera(self):
        nombre = self.ent_nom_carrera.get().strip()
        if not nombre:
            self.lbl_msj_carrera.configure(text="El nombre es obligatorio.", text_color=RED_COLOR)
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("INSERT INTO carrera (nombre) VALUES (%s)", (nombre,))
                conn.commit()
                self.ent_nom_carrera.delete(0, 'end')
                self.lbl_msj_carrera.configure(text="Carrera creada exitosamente.", text_color=GREEN_COLOR)
                self.cargar_carreras()
                self.cargar_opciones_carreras() # Refresca la pestaña de Pensum
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                self.lbl_msj_carrera.configure(text="Error: Esa carrera ya existe.", text_color=RED_COLOR)
            except Exception as e:
                conn.rollback()
                self.lbl_msj_carrera.configure(text=f"Error inesperado: {e}", text_color=RED_COLOR)
            finally:
                cur.close()
                conn.close()

    def cargar_carreras(self):
        for widget in self.tabla_carreras.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.tabla_carreras, text="Nombre de la Carrera", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=0, padx=5, pady=10, sticky="w")
        ctk.CTkLabel(self.tabla_carreras, text="Acciones", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=1, padx=5, pady=10, sticky="e")

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT id_carrera, nombre FROM carrera ORDER BY nombre;")
                for fila, (id_c, nombre) in enumerate(cur.fetchall(), start=1):
                    ctk.CTkLabel(self.tabla_carreras, text=nombre, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=5, sticky="w")
                    
                    btn_borrar = ctk.CTkButton(self.tabla_carreras, text="X", width=30, fg_color=RED_COLOR, text_color=TEXT_COLOR, command=lambda i=id_c: self.borrar_carrera(i))
                    btn_borrar.grid(row=fila, column=1, padx=5, pady=5, sticky="e")
            except Exception as e:
                print("Error cargando carreras:", e)
            finally:
                cur.close()
                conn.close()

    def borrar_carrera(self, id_carrera):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("DELETE FROM carrera WHERE id_carrera = %s", (id_carrera,))
                conn.commit()
                self.lbl_msj_carrera.configure(text="")
                self.cargar_carreras()
                self.cargar_opciones_carreras()
            except psycopg2.errors.ForeignKeyViolation:
                conn.rollback()
                self.lbl_msj_carrera.configure(text="Denegado: Hay estudiantes o un pensum activo en esta carrera.", text_color=RED_COLOR)
            except Exception as e:
                conn.rollback()
                print("Error borrando:", e)
            finally:
                cur.close()
                conn.close()

    # --- LÓGICA DE PERIODOS ---
    def construir_pestaña_periodos(self):
        frame_form = ctk.CTkFrame(self.tab_periodos, fg_color="transparent")
        frame_form.pack(fill="x", pady=10)

        self.ent_cod_periodo = ctk.CTkEntry(frame_form, placeholder_text="Código (Ej: 2026-I)", width=120, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.ent_cod_periodo.pack(side="left", padx=5)

        self.ent_inicio = ctk.CTkEntry(frame_form, placeholder_text="Inicio (YYYY-MM-DD)", width=150, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.ent_inicio.pack(side="left", padx=5)

        self.ent_fin = ctk.CTkEntry(frame_form, placeholder_text="Fin (YYYY-MM-DD)", width=150, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.ent_fin.pack(side="left", padx=5)

        btn_crear_periodo = ctk.CTkButton(frame_form, text="Crear Periodo", fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.crear_periodo)
        btn_crear_periodo.pack(side="left", padx=10)

        self.lbl_msj_periodo = ctk.CTkLabel(frame_form, text="", text_color=RED_COLOR)
        self.lbl_msj_periodo.pack(side="left", padx=10)

        self.tabla_periodos = ctk.CTkScrollableFrame(self.tab_periodos, fg_color=BG_COLOR)
        self.tabla_periodos.pack(fill="both", expand=True, pady=10)
        self.tabla_periodos.grid_columnconfigure((0,1,2,3), weight=1)
        self.tabla_periodos.grid_columnconfigure(4, weight=0)

        self.cargar_periodos()

    def crear_periodo(self):
        codigo = self.ent_cod_periodo.get().strip()
        inicio = self.ent_inicio.get().strip()
        fin = self.ent_fin.get().strip()

        if not all([codigo, inicio, fin]):
            self.lbl_msj_periodo.configure(text="Llena todos los campos.", text_color=RED_COLOR)
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("INSERT INTO periodo (codigo_periodo, fecha_inicio, fecha_fin, estado) VALUES (%s, %s, %s, 'Planificación')", (codigo, inicio, fin))
                conn.commit()
                self.ent_cod_periodo.delete(0, 'end')
                self.ent_inicio.delete(0, 'end')
                self.ent_fin.delete(0, 'end')
                self.lbl_msj_periodo.configure(text="Periodo creado.", text_color=GREEN_COLOR)
                self.cargar_periodos()
            except psycopg2.errors.CheckViolation:
                conn.rollback()
                self.lbl_msj_periodo.configure(text="Error: Fecha Fin debe ser mayor a Inicio.", text_color=RED_COLOR)
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                self.lbl_msj_periodo.configure(text="Error: Ese código ya existe.", text_color=RED_COLOR)
            except Exception as e:
                conn.rollback()
                self.lbl_msj_periodo.configure(text=f"Error: Revisar fechas.", text_color=RED_COLOR)
            finally:
                cur.close()
                conn.close()

    def cargar_periodos(self):
        for widget in self.tabla_periodos.winfo_children():
            widget.destroy()

        encabezados = ["Código", "Fecha Inicio", "Fecha Fin", "Estado", "Acciones"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_periodos, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT id_periodo, codigo_periodo, fecha_inicio, fecha_fin, estado FROM periodo ORDER BY id_periodo DESC;")
                periodos = cur.fetchall()

                for fila, (id_p, cod, inicio, fin, estado) in enumerate(periodos, start=1):
                    ctk.CTkLabel(self.tabla_periodos, text=cod, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_periodos, text=str(inicio), text_color=TEXT_COLOR).grid(row=fila, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_periodos, text=str(fin), text_color=TEXT_COLOR).grid(row=fila, column=2, padx=5, pady=5, sticky="w")
                    
                    color_estado = GREEN_COLOR if estado == 'Activo' else TEXT_COLOR
                    ctk.CTkLabel(self.tabla_periodos, text=estado, text_color=color_estado, font=ctk.CTkFont(weight="bold")).grid(row=fila, column=3, padx=5, pady=5, sticky="w")

                    frame_acciones = ctk.CTkFrame(self.tabla_periodos, fg_color="transparent")
                    frame_acciones.grid(row=fila, column=4, padx=5, pady=5, sticky="e")

                    # Botón para editar (disponible siempre)
                    btn_editar = ctk.CTkButton(frame_acciones, text="Editar", width=60, fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, text_color=TEXT_COLOR, command=lambda i=id_p: self.abrir_modal_editar_periodo(i))
                    btn_editar.pack(side="left", padx=2)

                    if estado != 'Activo':
                        btn_activar = ctk.CTkButton(frame_acciones, text="Activar", width=70, fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=lambda i=id_p: self.activar_periodo(i))
                        btn_activar.pack(side="left", padx=2)

            except Exception as e:
                print("Error cargando periodos:", e)
            finally:
                cur.close()
                conn.close()

    def abrir_modal_editar_periodo(self, id_periodo):
        VentanaEditarPeriodo(self, id_periodo, self.cargar_periodos)

    def activar_periodo(self, id_periodo):
        conn, cur = conectar_bd()
        if conn:
            try:
                # Transacción de 2 pasos: Apagar el viejo, encender el nuevo
                cur.execute("UPDATE periodo SET estado = 'Cerrado' WHERE estado = 'Activo'")
                cur.execute("UPDATE periodo SET estado = 'Activo' WHERE id_periodo = %s", (id_periodo,))
                conn.commit()
                self.cargar_periodos()
            except Exception as e:
                conn.rollback()
                print("Error activando:", e)
            finally:
                cur.close()
                conn.close()

    # --- LÓGICA DE PENSUM ---
    def construir_pestaña_pensum(self):
        frame_top = ctk.CTkFrame(self.tab_pensum, fg_color="transparent")
        frame_top.pack(fill="x", pady=10)

        ctk.CTkLabel(frame_top, text="Seleccione Carrera:", text_color=TEXT_COLOR).pack(side="left", padx=5)
        self.combo_carrera = ctk.CTkOptionMenu(frame_top, width=250, fg_color=BG_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, command=self.cargar_pensum)
        self.combo_carrera.pack(side="left", padx=10)

        self.btn_asignar = ctk.CTkButton(frame_top, text="+ Añadir Materia", fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, text_color=TEXT_COLOR, command=self.abrir_modal_pensum)
        self.btn_asignar.pack(side="right", padx=10)

        self.tabla_pensum = ctk.CTkScrollableFrame(self.tab_pensum, fg_color=BG_COLOR)
        self.tabla_pensum.pack(fill="both", expand=True, pady=10)
        self.tabla_pensum.grid_columnconfigure((1,2,3), weight=1)

        self.mapa_carreras = {}
        self.cargar_opciones_carreras()

    def cargar_opciones_carreras(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT id_carrera, nombre FROM carrera ORDER BY nombre;")
                carreras = cur.fetchall()
                self.mapa_carreras.clear()
                if carreras:
                    opciones = []
                    for id_c, nom in carreras:
                        opciones.append(nom)
                        self.mapa_carreras[nom] = id_c
                    self.combo_carrera.configure(values=opciones, state="normal")
                    self.combo_carrera.set(opciones[0])
                    self.cargar_pensum()
                else:
                    self.combo_carrera.configure(values=["Sin carreras registradas"], state="disabled")
                    self.combo_carrera.set("Sin carreras registradas")
                    for widget in self.tabla_pensum.winfo_children():
                        widget.destroy()
            finally:
                cur.close()
                conn.close()

    def cargar_pensum(self, *args):
        for widget in self.tabla_pensum.winfo_children():
            widget.destroy()

        seleccion = self.combo_carrera.get()
        if not seleccion or seleccion not in self.mapa_carreras: return

        id_carrera = self.mapa_carreras[seleccion]

        encabezados = ["Código", "Nombre del Curso", "Requisitos", "Acciones"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_pensum, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute('''
                    SELECT p.id_pensum, p.semestre_sugerido, c.codigo, c.nombre,
                           COALESCE(array_to_string(array_agg(DISTINCT cr.codigo), ', '), 'Ninguno') as prelaciones
                    FROM pensum p
                    JOIN curso c ON p.id_curso = c.id_curso
                    LEFT JOIN prelacion pr ON c.id_curso = pr.id_curso
                    LEFT JOIN curso cr ON pr.id_curso_requisito = cr.id_curso
                    WHERE p.id_carrera = %s
                    GROUP BY p.id_pensum, p.semestre_sugerido, c.codigo, c.nombre
                    ORDER BY p.semestre_sugerido, c.nombre
                ''', (id_carrera,))
                
                filas = cur.fetchall()
                
                fila_actual = 1
                semestre_actual = None
                
                for id_p, sem, cod, nom, prela_str in filas:
                    if sem != semestre_actual:
                        semestre_actual = sem
                        lbl_separador = ctk.CTkLabel(self.tabla_pensum, text=f"--- SEMESTRE {sem} ---", font=ctk.CTkFont(weight="bold", size=14), text_color=ACCENT_COLOR)
                        lbl_separador.grid(row=fila_actual, column=0, columnspan=4, pady=(15, 5), sticky="w")
                        fila_actual += 1

                    cod_str = cod if cod else "S/C"
                    ctk.CTkLabel(self.tabla_pensum, text=cod_str, text_color=TEXT_COLOR).grid(row=fila_actual, column=0, padx=15, pady=2, sticky="w")
                    ctk.CTkLabel(self.tabla_pensum, text=nom, text_color=TEXT_COLOR).grid(row=fila_actual, column=1, padx=5, pady=2, sticky="w")
                    ctk.CTkLabel(self.tabla_pensum, text=prela_str, text_color=TEXT_COLOR).grid(row=fila_actual, column=2, padx=5, pady=2, sticky="w")
                    
                    btn_quitar = ctk.CTkButton(self.tabla_pensum, text="X", width=30, fg_color=RED_COLOR, text_color=TEXT_COLOR, command=lambda id_pen=id_p: self.quitar_de_pensum(id_pen))
                    btn_quitar.grid(row=fila_actual, column=3, padx=5, pady=2, sticky="e")
                    
                    fila_actual += 1

            except Exception as e:
                print("Error cargando pensum:", e)
            finally:
                cur.close()
                conn.close()

    def abrir_modal_pensum(self):
        seleccion = self.combo_carrera.get()
        if seleccion in self.mapa_carreras:
            VentanaAgregarPensum(self, self.mapa_carreras[seleccion], seleccion, self.cargar_pensum)

    def quitar_de_pensum(self, id_pensum):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("DELETE FROM pensum WHERE id_pensum = %s", (id_pensum,))
                conn.commit()
                self.cargar_pensum()
            except Exception as e:
                print("Error borrando de pensum:", e)
            finally:
                cur.close()
                conn.close()