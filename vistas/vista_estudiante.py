import customtkinter as ctk
import psycopg2
from conexion import conectar_bd

BG_COLOR = "#282828"
SIDEBAR_COLOR = "#3c3836"
ACCENT_COLOR = "#d79921"
TEXT_COLOR = "#ebdbb2"
RED_COLOR = "#cc241d"
GREEN_COLOR = "#98971a"
BLUE_COLOR = "#458588"

# ==========================================
# VENTANA MODAL: ELEGIR SECCIÓN E INSCRIBIR
# ==========================================
class VentanaElegirSeccion(ctk.CTkToplevel):
    def __init__(self, master, id_curso, nombre_curso, costo, id_periodo, id_estudiante, callback_actualizar):
        super().__init__(master)
        self.title(f"Secciones: {nombre_curso}")
        self.geometry("750x400")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()

        self.id_curso = id_curso
        self.costo = costo
        self.id_periodo = id_periodo
        self.id_estudiante = id_estudiante
        self.callback_actualizar = callback_actualizar

        ctk.CTkLabel(self, text=f"Secciones disponibles para:\n{nombre_curso}", font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT_COLOR).pack(pady=(15, 5))
        ctk.CTkLabel(self, text=f"Costo a descontar: ${costo:.2f}", font=ctk.CTkFont(size=14), text_color=TEXT_COLOR).pack(pady=(0, 10))

        self.lbl_msj = ctk.CTkLabel(self, text="", text_color=GREEN_COLOR)
        self.lbl_msj.pack(pady=5)

        self.tabla_secciones = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_secciones.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_secciones.grid_columnconfigure((0,1,2,3), weight=1)
        self.tabla_secciones.grid_columnconfigure(4, weight=0)

        self.cargar_secciones()

    def cargar_secciones(self):
        encabezados = ["Sec.", "Profesor", "Horario", "Cupo", "Acción"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_secciones, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT s.id_seccion, s.identificador, p.nombres, p.apellidos, c.cupo_maximo,
                           (SELECT COUNT(*) FROM inscripcion i WHERE i.id_seccion = s.id_seccion) as inscritos,
                           COALESCE(array_to_string(array_agg(h.dia_semana || ' ' || substr(h.hora_inicio::text, 1, 5) || '-' || substr(h.hora_fin::text, 1, 5) ORDER BY h.id_horario), ' | '), 'Sin asignar') as horario_str
                    FROM seccion s
                    JOIN curso c ON s.id_curso = c.id_curso
                    JOIN profesor p ON s.id_profesor = p.id_profesor
                    LEFT JOIN horario h ON s.id_seccion = h.id_seccion
                    WHERE s.id_periodo = %s AND s.id_curso = %s
                    GROUP BY s.id_seccion, c.nombre, p.nombres, p.apellidos, c.cupo_maximo
                    ORDER BY s.identificador
                '''
                cur.execute(query, (self.id_periodo, self.id_curso))
                secciones = cur.fetchall()

                if not secciones:
                    ctk.CTkLabel(self.tabla_secciones, text="No hay secciones abiertas para esta materia.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=5, pady=20)

                for fila_idx, (id_sec, ident, nom_prof, ape_prof, cupo_max, inscritos, horario) in enumerate(secciones, start=1):
                    ctk.CTkLabel(self.tabla_secciones, text=ident, text_color=TEXT_COLOR).grid(row=fila_idx, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_secciones, text=f"{ape_prof}, {nom_prof}", text_color=TEXT_COLOR).grid(row=fila_idx, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_secciones, text=horario, text_color=TEXT_COLOR).grid(row=fila_idx, column=2, padx=5, pady=5, sticky="w")
                    
                    color_cupo = RED_COLOR if inscritos >= cupo_max else TEXT_COLOR
                    ctk.CTkLabel(self.tabla_secciones, text=f"{inscritos} / {cupo_max}", text_color=color_cupo, font=ctk.CTkFont(weight="bold")).grid(row=fila_idx, column=3, padx=5, pady=5, sticky="w")

                    frame_acc = ctk.CTkFrame(self.tabla_secciones, fg_color="transparent")
                    frame_acc.grid(row=fila_idx, column=4, padx=5, pady=5, sticky="e")

                    if inscritos >= cupo_max:
                        btn = ctk.CTkButton(frame_acc, text="Lleno", width=80, fg_color=RED_COLOR, text_color=TEXT_COLOR, state="disabled")
                    else:
                        btn = ctk.CTkButton(frame_acc, text="Inscribir", width=80, fg_color=BLUE_COLOR, text_color=TEXT_COLOR, font=ctk.CTkFont(weight="bold"), command=lambda s=id_sec: self.procesar_inscripcion(s))
                    btn.pack(side="left", padx=2)

            except Exception as e:
                print("Error cargando secciones de la materia:", e)
            finally:
                cur.close()
                conn.close()

    def procesar_inscripcion(self, id_seccion):
        self.lbl_msj.configure(text="")
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT saldo FROM estudiante WHERE id_estudiante = %s", (self.id_estudiante,))
                saldo_actual = cur.fetchone()[0]

                if saldo_actual < self.costo:
                    self.lbl_msj.configure(text=f"Saldo insuficiente. Necesitas ${self.costo:.2f}", text_color=RED_COLOR)
                    return

                cur.execute(
                    "INSERT INTO inscripcion (id_estudiante, id_seccion, costo_cobrado, estado) VALUES (%s, %s, %s, 'Inscrito')",
                    (self.id_estudiante, id_seccion, self.costo)
                )
                cur.execute(
                    "UPDATE estudiante SET saldo = saldo - %s WHERE id_estudiante = %s",
                    (self.costo, self.id_estudiante)
                )
                conn.commit()

                self.lbl_msj.configure(text="¡Inscrito correctamente!", text_color=GREEN_COLOR)
                self.callback_actualizar()
                self.after(1000, self.destroy) 

            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                self.lbl_msj.configure(text="Error: Ya estás inscrito en esta materia.", text_color=RED_COLOR)
            except Exception as e:
                conn.rollback()
                self.lbl_msj.configure(text=f"Error: {e}", text_color=RED_COLOR)
            finally:
                cur.close()
                conn.close()


# ==========================================
# PANEL PRINCIPAL: VISTA ESTUDIANTE
# ==========================================
class VistaEstudiante(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_COLOR)
        
        # --- HEADER / SIMULADOR DE SESIÓN ---
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.pack(fill="x", padx=20, pady=(20, 10))

        frame_top = ctk.CTkFrame(frame_header, fg_color="transparent")
        frame_top.pack(fill="x")
        
        ctk.CTkLabel(frame_top, text="Portal Estudiantil", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR).pack(side="left")
        self.lbl_periodo = ctk.CTkLabel(frame_top, text="Periodo: Cargando...", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR)
        self.lbl_periodo.pack(side="right", padx=10)

        frame_ctrl = ctk.CTkFrame(frame_header, fg_color="transparent")
        frame_ctrl.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(frame_ctrl, text="Estudiante:", text_color=TEXT_COLOR).pack(side="left", padx=(0, 5))
        self.combo_estudiante = ctk.CTkOptionMenu(frame_ctrl, width=220, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, command=self.al_cambiar_estudiante)
        self.combo_estudiante.pack(side="left")

        ctk.CTkLabel(frame_ctrl, text="Carrera:", text_color=TEXT_COLOR).pack(side="left", padx=(20, 5))
        self.combo_carrera = ctk.CTkOptionMenu(frame_ctrl, width=220, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, command=self.al_cambiar_carrera)
        self.combo_carrera.pack(side="left")

        # --- TABS ---
        self.tabview = ctk.CTkTabview(self, fg_color=SIDEBAR_COLOR, segmented_button_selected_color=ACCENT_COLOR, segmented_button_selected_hover_color="#b57614")
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        self.tab_perfil = self.tabview.add("Mi Perfil")
        self.tab_kardex = self.tabview.add("Mi Kárdex") # NUEVA PESTAÑA
        self.tab_horario = self.tabview.add("Mi Horario")
        self.tab_inscripcion = self.tabview.add("Inscripciones")

        self.id_estudiante_actual = None
        self.id_carrera_actual = None
        self.id_periodo_activo = None
        
        self.mapa_estudiantes = {}
        self.mapa_carreras = {}

        self.construir_pestaña_perfil()
        self.construir_pestaña_kardex()
        self.construir_pestaña_horario()
        self.construir_pestaña_inscripcion()

        self.inicializar_datos()

    def inicializar_datos(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT id_periodo, codigo_periodo FROM periodo WHERE estado = 'Activo'")
                periodo = cur.fetchone()
                if periodo:
                    self.id_periodo_activo = periodo[0]
                    self.lbl_periodo.configure(text=f"Periodo Activo: {periodo[1]}")
                else:
                    self.lbl_periodo.configure(text="No hay periodo activo", text_color=RED_COLOR)

                cur.execute("SELECT id_estudiante, cedula, nombres, apellidos FROM estudiante ORDER BY apellidos")
                estudiantes = cur.fetchall()
                if estudiantes:
                    opciones = []
                    for id_e, ced, nom, ape in estudiantes:
                        texto = f"{ape}, {nom} ({ced})"
                        opciones.append(texto)
                        self.mapa_estudiantes[texto] = id_e
                    
                    self.combo_estudiante.configure(values=opciones)
                    self.combo_estudiante.set(opciones[0])
                    self.al_cambiar_estudiante(opciones[0])
                else:
                    self.combo_estudiante.configure(values=["No hay estudiantes registrados"])
                    self.combo_estudiante.set("No hay estudiantes registrados")

            except Exception as e:
                print("Error de inicialización:", e)
            finally:
                cur.close()
                conn.close()

    def al_cambiar_estudiante(self, seleccion):
        if seleccion in self.mapa_estudiantes:
            self.id_estudiante_actual = self.mapa_estudiantes[seleccion]
            self.cargar_perfil()
            self.cargar_kardex()
            self.actualizar_carreras_estudiante()

    def actualizar_carreras_estudiante(self):
        conn, cur = conectar_bd()
        self.mapa_carreras.clear()
        opciones = []
        if conn and self.id_estudiante_actual:
            try:
                cur.execute('''
                    SELECT c.id_carrera, c.nombre 
                    FROM expediente_carrera ec
                    JOIN carrera c ON ec.id_carrera = c.id_carrera
                    WHERE ec.id_estudiante = %s AND ec.estado = 'Activo'
                    ORDER BY c.nombre
                ''', (self.id_estudiante_actual,))
                for id_c, nom in cur.fetchall():
                    self.mapa_carreras[nom] = id_c
                    opciones.append(nom)
            except Exception as e:
                print("Error cargando carreras del estudiante:", e)
            finally:
                cur.close()
                conn.close()
        
        if opciones:
            self.combo_carrera.configure(values=opciones, state="normal")
            self.combo_carrera.set(opciones[0])
            self.al_cambiar_carrera(opciones[0])
        else:
            self.combo_carrera.configure(values=["No inscrito en ninguna carrera"], state="disabled")
            self.combo_carrera.set("No inscrito en ninguna carrera")
            self.id_carrera_actual = None
            self.cargar_horario()
            self.cargar_oferta_academica()

    def al_cambiar_carrera(self, seleccion=None):
        if not seleccion:
            seleccion = self.combo_carrera.get()
        if seleccion in self.mapa_carreras:
            self.id_carrera_actual = self.mapa_carreras[seleccion]
        else:
            self.id_carrera_actual = None
        self.cargar_horario()
        self.cargar_oferta_academica()

    def actualizar_tablas(self):
        self.cargar_perfil()
        self.cargar_kardex()
        self.cargar_horario()
        self.cargar_oferta_academica()

    # ==========================================
    # PESTAÑA: MI PERFIL
    # ==========================================
    def construir_pestaña_perfil(self):
        self.lbl_nombre_perfil = ctk.CTkLabel(self.tab_perfil, text="", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT_COLOR)
        self.lbl_nombre_perfil.pack(pady=(20, 5))

        self.lbl_datos_perfil = ctk.CTkLabel(self.tab_perfil, text="", text_color=TEXT_COLOR)
        self.lbl_datos_perfil.pack(pady=5)

        self.frame_saldo = ctk.CTkFrame(self.tab_perfil, fg_color=BG_COLOR, corner_radius=10)
        self.frame_saldo.pack(pady=15, padx=50, fill="x")
        self.lbl_saldo = ctk.CTkLabel(self.frame_saldo, text="Saldo Disponible: $0.00", font=ctk.CTkFont(size=18, weight="bold"), text_color=GREEN_COLOR)
        self.lbl_saldo.pack(pady=15)

        ctk.CTkLabel(self.tab_perfil, text="Mis Carreras", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_COLOR).pack(pady=(10, 5))
        
        self.tabla_carreras = ctk.CTkScrollableFrame(self.tab_perfil, fg_color=BG_COLOR, height=150)
        self.tabla_carreras.pack(padx=50, pady=5, fill="x")
        self.tabla_carreras.grid_columnconfigure((0,1), weight=1)

    def cargar_perfil(self):
        if not self.id_estudiante_actual: return

        for widget in self.tabla_carreras.winfo_children():
            widget.destroy()

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT cedula, email, saldo FROM estudiante WHERE id_estudiante = %s", (self.id_estudiante_actual,))
                datos = cur.fetchone()
                if datos:
                    self.lbl_nombre_perfil.configure(text=self.combo_estudiante.get())
                    self.lbl_datos_perfil.configure(text=f"C.I: {datos[0]} | Email: {datos[1]}")
                    self.lbl_saldo.configure(text=f"Saldo Disponible: ${datos[2]:.2f}")

                cur.execute('''
                    SELECT c.nombre, ec.estado, ec.fecha_inscripcion 
                    FROM expediente_carrera ec
                    JOIN carrera c ON ec.id_carrera = c.id_carrera
                    WHERE ec.id_estudiante = %s
                ''', (self.id_estudiante_actual,))
                
                carreras = cur.fetchall()
                if not carreras:
                    ctk.CTkLabel(self.tabla_carreras, text="No estás inscrito en ninguna carrera.", text_color=TEXT_COLOR).grid(row=0, column=0, pady=10)
                else:
                    ctk.CTkLabel(self.tabla_carreras, text="Carrera", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=5)
                    ctk.CTkLabel(self.tabla_carreras, text="Estado", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=1, sticky="w", padx=10, pady=5)
                    
                    for i, (nom, est, fecha) in enumerate(carreras, start=1):
                        ctk.CTkLabel(self.tabla_carreras, text=nom, text_color=TEXT_COLOR).grid(row=i, column=0, sticky="w", padx=10, pady=2)
                        ctk.CTkLabel(self.tabla_carreras, text=est, text_color=TEXT_COLOR).grid(row=i, column=1, sticky="w", padx=10, pady=2)
            except Exception as e:
                print("Error cargando perfil:", e)
            finally:
                cur.close()
                conn.close()

    # ==========================================
    # PESTAÑA: MI KÁRDEX (HISTORIAL DE NOTAS)
    # ==========================================
    def construir_pestaña_kardex(self):
        self.tabla_kardex = ctk.CTkScrollableFrame(self.tab_kardex, fg_color=BG_COLOR)
        self.tabla_kardex.pack(padx=20, pady=20, fill="both", expand=True)
        self.tabla_kardex.grid_columnconfigure((0,1,2,3), weight=1)

    def cargar_kardex(self):
        for widget in self.tabla_kardex.winfo_children():
            widget.destroy()

        if not self.id_estudiante_actual: return

        encabezados = ["Periodo", "Materia", "Nota Acumulada", "Estado"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_kardex, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                # Motor matemático: Suma de (nota_numerica * ponderacion / 100)
                query = '''
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
                cur.execute(query, (self.id_estudiante_actual,))
                historial = cur.fetchall()

                if not historial:
                    ctk.CTkLabel(self.tabla_kardex, text="Aún no tienes historial académico.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=4, pady=20)

                for fila_idx, (periodo, curso, nota_acumulada, porcentaje_evaluado) in enumerate(historial, start=1):
                    # Convertimos de Decimal a float
                    nota_acumulada = float(nota_acumulada)
                    porcentaje_evaluado = float(porcentaje_evaluado)

                    # Lógica de Estado: Solo se aprueba si el profesor evaluó el 100% y sacaste >= 5.0 (Base 10)
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

                    ctk.CTkLabel(self.tabla_kardex, text=periodo, text_color=TEXT_COLOR).grid(row=fila_idx, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_kardex, text=curso, text_color=TEXT_COLOR).grid(row=fila_idx, column=1, padx=5, pady=5, sticky="w")
                    
                    # Mostramos la nota sobre 10
                    ctk.CTkLabel(self.tabla_kardex, text=f"{nota_acumulada:.2f} / 10", text_color=TEXT_COLOR, font=ctk.CTkFont(weight="bold")).grid(row=fila_idx, column=2, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_kardex, text=estado_texto, text_color=color_estado, font=ctk.CTkFont(weight="bold")).grid(row=fila_idx, column=3, padx=5, pady=5, sticky="w")

            except Exception as e:
                print("Error cargando kardex:", e)
            finally:
                cur.close()
                conn.close()

    # ==========================================
    # PESTAÑA: MI HORARIO
    # ==========================================
    def construir_pestaña_horario(self):
        self.tabla_mi_horario = ctk.CTkScrollableFrame(self.tab_horario, fg_color=BG_COLOR)
        self.tabla_mi_horario.pack(padx=20, pady=20, fill="both", expand=True)
        self.tabla_mi_horario.grid_columnconfigure((0,1,2,3), weight=1)

    def cargar_horario(self):
        for widget in self.tabla_mi_horario.winfo_children():
            widget.destroy()

        if not self.id_estudiante_actual or not self.id_periodo_activo or not self.id_carrera_actual: 
            return

        encabezados = ["Materia", "Sección", "Profesor", "Horario"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_mi_horario, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT c.nombre, s.identificador, p.nombres, p.apellidos,
                           COALESCE(array_to_string(array_agg(h.dia_semana || ' ' || substr(h.hora_inicio::text, 1, 5) || '-' || substr(h.hora_fin::text, 1, 5) ORDER BY h.id_horario), ' | '), 'Sin asignar')
                    FROM inscripcion i
                    JOIN seccion s ON i.id_seccion = s.id_seccion
                    JOIN curso c ON s.id_curso = c.id_curso
                    JOIN profesor p ON s.id_profesor = p.id_profesor
                    JOIN pensum pe ON c.id_curso = pe.id_curso
                    LEFT JOIN horario h ON s.id_seccion = h.id_seccion
                    WHERE i.id_estudiante = %s AND s.id_periodo = %s AND pe.id_carrera = %s
                    GROUP BY c.nombre, s.identificador, p.nombres, p.apellidos
                    ORDER BY c.nombre
                '''
                cur.execute(query, (self.id_estudiante_actual, self.id_periodo_activo, self.id_carrera_actual))
                clases = cur.fetchall()

                if not clases:
                    ctk.CTkLabel(self.tabla_mi_horario, text="No tienes clases inscritas de esta carrera en este periodo.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=4, pady=20)

                for fila_idx, (curso, sec, nom_prof, ape_prof, horario) in enumerate(clases, start=1):
                    ctk.CTkLabel(self.tabla_mi_horario, text=curso, text_color=TEXT_COLOR).grid(row=fila_idx, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_mi_horario, text=sec, text_color=TEXT_COLOR).grid(row=fila_idx, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_mi_horario, text=f"{ape_prof}, {nom_prof}", text_color=TEXT_COLOR).grid(row=fila_idx, column=2, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_mi_horario, text=horario, text_color=TEXT_COLOR).grid(row=fila_idx, column=3, padx=5, pady=5, sticky="w")

            except Exception as e:
                print("Error cargando mi horario:", e)
            finally:
                cur.close()
                conn.close()

    # ==========================================
    # PESTAÑA: INSCRIPCIONES (Catálogo validado)
    # ==========================================
    def construir_pestaña_inscripcion(self):
        self.tabla_oferta = ctk.CTkScrollableFrame(self.tab_inscripcion, fg_color=BG_COLOR)
        self.tabla_oferta.pack(padx=20, pady=20, fill="both", expand=True)
        self.tabla_oferta.grid_columnconfigure((0,1), weight=1)
        self.tabla_oferta.grid_columnconfigure(2, weight=0)

    def cargar_oferta_academica(self):
        for widget in self.tabla_oferta.winfo_children():
            widget.destroy()

        if not self.id_periodo_activo or not self.id_estudiante_actual or not self.id_carrera_actual:
            ctk.CTkLabel(self.tabla_oferta, text="Faltan datos de sesión o no hay carrera seleccionada.", text_color=RED_COLOR).grid(row=0, column=0, pady=20)
            return

        encabezados = ["Materia", "Costo", "Acciones"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_oferta, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT DISTINCT c.id_curso, c.nombre, c.costo
                    FROM seccion s
                    JOIN curso c ON s.id_curso = c.id_curso
                    WHERE s.id_periodo = %s
                      AND c.id_curso IN (
                          SELECT p.id_curso 
                          FROM pensum p
                          WHERE p.id_carrera = %s
                      )
                      AND c.id_curso NOT IN (
                          SELECT s2.id_curso
                          FROM inscripcion i
                          JOIN seccion s2 ON i.id_seccion = s2.id_seccion
                          WHERE i.id_estudiante = %s AND s2.id_periodo = %s
                      )
                      AND NOT EXISTS (
                          SELECT 1 FROM prelacion pr
                          WHERE pr.id_curso = c.id_curso
                          AND pr.id_curso_requisito NOT IN (
                              SELECT sec_aprob.id_curso
                              FROM calificacion cal
                              JOIN evaluacion ev ON cal.id_evaluacion = ev.id_evaluacion
                              JOIN seccion sec_aprob ON ev.id_seccion = sec_aprob.id_seccion
                              WHERE cal.id_estudiante = %s AND cal.nota_conceptual = 'Aprobado'
                          )
                      )
                    ORDER BY c.nombre
                '''
                cur.execute(query, (
                    self.id_periodo_activo, 
                    self.id_carrera_actual, 
                    self.id_estudiante_actual, 
                    self.id_periodo_activo, 
                    self.id_estudiante_actual
                ))
                oferta = cur.fetchall()

                if not oferta:
                    ctk.CTkLabel(self.tabla_oferta, text="No hay materias disponibles en esta carrera (O te faltan prelaciones).", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=3, pady=20)

                for fila_idx, (id_curso, curso, costo) in enumerate(oferta, start=1):
                    ctk.CTkLabel(self.tabla_oferta, text=curso, text_color=TEXT_COLOR).grid(row=fila_idx, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_oferta, text=f"${costo:.2f}", text_color=TEXT_COLOR).grid(row=fila_idx, column=1, padx=5, pady=5, sticky="w")

                    btn = ctk.CTkButton(self.tabla_oferta, text="Ver Secciones", width=100, fg_color=ACCENT_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=lambda c=id_curso, n=curso, p=costo: VentanaElegirSeccion(self, c, n, p, self.id_periodo_activo, self.id_estudiante_actual, self.actualizar_tablas))
                    btn.grid(row=fila_idx, column=2, padx=5, pady=5, sticky="e")

            except Exception as e:
                print("Error cargando oferta:", e)
            finally:
                cur.close()
                conn.close()