
G28 W ; home all
G90 ;absolute positioning
G0 Z10 X5 Y210 F6000 ; home at corner
G28 X Y
G1 Z20.0 F1200
G28 X Y
G1 Z30.0 F1200
G28 X Y
G1 Z40.0 F1200
G28 X Y
G1 Z50.0 F1200
G28 X Y
G1 Z60.0 F1200
G28 X Y
G1 Z70.0 F1200
G28 X Y
G1 Z80.0 F1200
G28 X Y
G1 Z90.0 F1200
G28 X Y
G1 Z100.0 F1200
G28 X Y
G1 Z120.0 F1200
G28 X Y
G1 Z130.0 F1200
G28 X Y
G1 Z140.0 F1200
G28 X Y
G1 Z150.0 F1200
G28 X Y
G1 Z160.0 F1200
G28 X Y
G1 Z170.0 F1200
G28 X Y
G1 Z180.0 F1200
G28 X Y
G1 Z190.0 F1200
G28 X Y
G1 Z200.0 F1200
G28 X Y
G1 Z210.0 F1200
G28 X Y
G1 Z230.0 F1200
M104 S0 T0
M18
M107
M140 S0
M77
; custom gcode end: end_gcode
M73 P100 R0
; filament used [mm] = 7390.08
; filament used [cm3] = 17.78
; filament used [g] = 18.84
; filament cost = 0.02

; total filament used [g] = 18.84
; total filament cost = 0.02
; estimated printing time (normal mode) = 1h 11m 57s

; allow_empty_layers = 0
; avoid_crossing_not_first_layer = 1
; avoid_crossing_perimeters = 0
; bed_custom_model = D:\\Диван-Кровать\\3д_модели\\sapphire pro bed.STL
; bed_custom_texture = 
; bed_shape = 0x0,220x0,220x220,0x220
; bed_temperature = 80
; before_layer_gcode = 
; between_objects_gcode = 
; bottom_fill_pattern = monotonic
; bottom_solid_layers = 4
; bottom_solid_min_thickness = 0.5
; bridge_acceleration = 0
; bridge_angle = 0
; bridge_fan_speed = 100
; bridge_flow_ratio = 100%
; bridge_overlap = 100%
; bridge_speed = 20
; bridge_speed_internal = 150%
; bridged_infill_margin = 200%
; brim_ears = 0
; brim_ears_max_angle = 125
; brim_ears_pattern = concentric
; brim_inside_holes = 0
; brim_offset = 0
; brim_width = 0
; brim_width_interior = 0
; chamber_temperature = 0
; clip_multipart_objects = 1
; color_change_gcode = M600
; complete_objects = 0
; complete_objects_one_skirt = 0
; complete_objects_sort = object
; cooling = 1
; cooling_tube_length = 5
; cooling_tube_retraction = 91.5
; curve_smoothing_angle_concave = 0
; curve_smoothing_angle_convex = 0
; curve_smoothing_cutoff_dist = 2
; curve_smoothing_precision = 0
; default_acceleration = 1500
; default_filament_profile = "Basic PLA"
; default_print_profile = 0.20mm NORMAL .4N
; deretract_speed = 60
; disable_fan_first_layers = 1
; dont_support_bridges = 1
; draft_shield = 0
; duplicate_distance = 6
; end_filament_gcode = "; Filament-specific end gcode \n;END gcode for filament\n"
; end_gcode = G90 ;absolute positioning\nG28 X Y\nG1 Z230.0 F1200\nM104 S0 T0\nM18\nM107\nM140 S0\nM77
; enforce_full_fill_volume = 0
; ensure_vertical_shell_thickness = 0
; exact_last_layer_height = 0
; external_infill_margin = 150%
; external_perimeter_cut_corners = 0%
; external_perimeter_extrusion_width = 0.45
; external_perimeter_fan_speed = -1
; external_perimeter_overlap = 100%
; external_perimeter_speed = 60%
; external_perimeters_first = 0
; external_perimeters_hole = 1
; external_perimeters_nothole = 1
; external_perimeters_vase = 0
; extra_loading_move = -2
; extra_perimeters = 0
; extra_perimeters_odd_layers = 0
; extra_perimeters_overhangs = 0
; extruder_clearance_height = 20
; extruder_clearance_radius = 20
; extruder_colour = ""
; extruder_fan_offset = 0%
; extruder_offset = 0x0
; extruder_temperature_offset = 0
; extrusion_axis = E
; extrusion_multiplier = 1
; extrusion_width = 0.45
; fan_always_on = 1
; fan_below_layer_time = 5
; fan_kickstart = 0
; fan_speedup_overhangs = 1
; fan_speedup_time = -1
; feature_gcode = 
; filament_colour = #29B2B2
; filament_cooling_final_speed = 3.4
; filament_cooling_initial_speed = 2.2
; filament_cooling_moves = 4
; filament_cooling_zone_pause = 0
; filament_cost = 1
; filament_density = 1.06
; filament_diameter = 1.75
; filament_dip_extraction_speed = 70
; filament_dip_insertion_speed = 33
; filament_enable_toolchange_part_fan = 0
; filament_enable_toolchange_temp = 0
; filament_load_time = 0
; filament_loading_speed = 28
; filament_loading_speed_start = 3
; filament_max_speed = 0
; filament_max_volumetric_speed = 0
; filament_max_wipe_tower_speed = 0
; filament_melt_zone_pause = 0
; filament_minimal_purge_on_wipe_tower = 15
; filament_notes = ""
; filament_ramming_parameters = "120 100 6.6 6.8 7.2 7.6 7.9 8.2 8.7 9.4 9.9 10.0| 0.05 6.6 0.45 6.8 0.95 7.8 1.45 8.3 1.95 9.7 2.45 10 2.95 7.6 3.45 7.6 3.95 7.6 4.45 7.6 4.95 7.6"
; filament_settings_id = "PETG fdZAPLAST"
; filament_shrink = 100%
; filament_skinnydip_distance = 31
; filament_soluble = 0
; filament_spool_weight = 0
; filament_toolchange_delay = 0
; filament_toolchange_part_fan_speed = 50
; filament_toolchange_temp = 200
; filament_type = PET
; filament_unload_time = 0
; filament_unloading_speed = 90
; filament_unloading_speed_start = 100
; filament_use_fast_skinnydip = 0
; filament_use_skinnydip = 0
; filament_vendor = (Unknown)
; filament_wipe_advanced_pigment = 0.5
; fill_angle = 45
; fill_angle_increment = 0
; fill_density = 18%
; fill_pattern = gyroid
; fill_smooth_distribution = 10%
; fill_smooth_width = 50%
; fill_top_flow_ratio = 100%
; first_layer_acceleration = 0
; first_layer_bed_temperature = 80
; first_layer_extrusion_width = 105%
; first_layer_flow_ratio = 100%
; first_layer_height = 60%
; first_layer_infill_speed = 80%
; first_layer_size_compensation = 0
; first_layer_speed = 40
; first_layer_temperature = 240
; gap_fill = 1
; gap_fill_min_area = 100%
; gap_fill_overlap = 100%
; gap_fill_speed = 60
; gcode_comments = 0
; gcode_flavor = marlin
; gcode_label_objects = 1
; high_current_on_filament_swap = 0
; hole_size_compensation = 0
; hole_size_threshold = 100
; hole_to_polyhole = 0
; host_type = octoprint
; infill_acceleration = 0
; infill_anchor = 0
; infill_connection = connected
; infill_connection_bottom = connected
; infill_connection_solid = connected
; infill_connection_top = connected
; infill_dense = 0
; infill_dense_algo = autosmall
; infill_every_layers = 1
; infill_extruder = 1
; infill_extrusion_width = 0.45
; infill_first = 0
; infill_only_where_needed = 0
; infill_overlap = 25%
; infill_speed = 80
; interface_shells = 0
; ironing = 0
; ironing_flowrate = 15%
; ironing_spacing = 0.1
; ironing_speed = 15
; ironing_type = top
; layer_gcode = ;AFTER_LAYER_CHANGE\n;[layer_z]
; layer_height = 0.2
; machine_limits_usage = time_estimate_only
; machine_max_acceleration_e = 1000,5000
; machine_max_acceleration_extruding = 1300,1250
; machine_max_acceleration_retracting = 1000,1250
; machine_max_acceleration_travel = 1500,1250
; machine_max_acceleration_x = 1400,1000
; machine_max_acceleration_y = 1400,1000
; machine_max_acceleration_z = 100,200
; machine_max_feedrate_e = 75,120
; machine_max_feedrate_x = 200,200
; machine_max_feedrate_y = 200,200
; machine_max_feedrate_z = 10,12
; machine_max_jerk_e = 2.5,2.5
; machine_max_jerk_x = 20,10
; machine_max_jerk_y = 20,10
; machine_max_jerk_z = 0.2,0.4
; machine_min_extruding_rate = 0,0
; machine_min_travel_rate = 0,0
; max_fan_speed = 100
; max_layer_height = 0.3
; max_print_height = 230
; max_print_speed = 100
; max_speed_reduction = 30%
; max_volumetric_speed = 0
; milling_after_z = 200%
; milling_extra_size = 150%
; milling_post_process = 0
; milling_speed = 30
; milling_toolchange_end_gcode = 
; milling_toolchange_start_gcode = 
; min_fan_speed = 80
; min_layer_height = 0.1
; min_length = 0.035
; min_print_speed = 10
; min_skirt_length = 0
; min_width_top_surface = 200%
; model_precision = 0.0001
; no_perimeter_unsupported_algo = none
; notes = 
; nozzle_diameter = 0.4
; only_one_perimeter_top = 1
; only_retract_when_crossing_perimeters = 1
; ooze_prevention = 0
; output_filename_format = [input_filename_base].gcode
; over_bridge_flow_ratio = 100%
; overhangs_reverse = 0
; overhangs_reverse_threshold = 250%
; overhangs_speed = 100%
; overhangs_width = 10
; overhangs_width_speed = 50%
; parking_pos_retraction = 92
; pause_print_gcode = M601
; perimeter_acceleration = 0
; perimeter_bonding = 0%
; perimeter_extruder = 1
; perimeter_extrusion_width = 0.45
; perimeter_loop = 0
; perimeter_loop_seam = rear
; perimeter_overlap = 100%
; perimeter_speed = 70
; perimeters = 5
; post_process = 
; print_extrusion_multiplier = 100%
; print_retract_length = -1
; print_retract_lift = -1
; print_settings_id = Sapphire Pro
; print_temperature = 0
; printer_model = Bowden_1.75mm
; printer_notes = 
; printer_settings_id = Sapphire Pro
; printer_technology = FFF
; printer_variant = 0.4
; printer_vendor = 
; raft_layers = 0
; remaining_times = 1
; resolution = 0
; retract_before_travel = 1
; retract_before_wipe = 0%
; retract_layer_change = 1
; retract_length = 4.5
; retract_length_toolchange = 10
; retract_lift = 0
; retract_lift_above = 0
; retract_lift_below = 9999
; retract_lift_first_layer = 0
; retract_lift_top = "All surfaces"
; retract_restart_extra = 0
; retract_restart_extra_toolchange = 0
; retract_speed = 60
; seam_angle_cost = 100%
; seam_position = hidden
; seam_travel_cost = 20%
; silent_mode = 0
; single_extruder_multi_material = 0
; single_extruder_multi_material_priming = 1
; skirt_distance = 0
; skirt_extrusion_width = 0
; skirt_height = 4
; skirts = 0
; slice_closing_radius = 0.049
; slowdown_below_layer_time = 5
; small_perimeter_max_length = 30
; small_perimeter_min_length = 5
; small_perimeter_speed = 30
; solid_fill_pattern = rectilineargapfill
; solid_infill_below_area = 25
; solid_infill_every_layers = 0
; solid_infill_extruder = 1
; solid_infill_extrusion_width = 0.45
; solid_infill_speed = 90%
; spiral_vase = 0
; standby_temperature_delta = -5
; start_filament_gcode = "; Filament gcode\n"
; start_gcode = M115 U3.1.0 ; tell printer latest fw version\nM83  ; extruder relative mode\nM77\nM75\nM204 S[machine_max_acceleration_extruding] T[machine_max_acceleration_retracting] ; ENDER3 firmware may only supports the old M204 format\nM104 S{first_layer_temperature[initial_extruder]+extruder_temperature_offset[initial_extruder]} ; set extruder temp\nM140 S[first_layer_bed_temperature] ; set bed temp\nM190 S[first_layer_bed_temperature] ; wait for bed temp\nM109 S[first_layer_temperature] ; wait for extruder temp\nG28 W ; home all\n;\nG90 ;absolute positioning\nG0 Z10 X5 Y210 F6000 ; home at corner\nG91; relative pos\nG1 E30 F200; extrude. clear nozzle\nG90 ;absolute positioning\nG0 Z0.1 X10 Y180 F2000 ; diagonal lift nozzle to bed\nG91; relative pos\nG1 Y-100 E10 F1000; extrude line\nG1 X50 F8000; wipe\nG90 ;absolute positioning
; support_material = 1
; support_material_angle = 0
; support_material_auto = 0
; support_material_buildplate_only = 0
; support_material_contact_distance_bottom = 0.2
; support_material_contact_distance_top = 0.2
; support_material_contact_distance_type = plane
; support_material_enforce_layers = 0
; support_material_extruder = 1
; support_material_extrusion_width = 0.35
; support_material_interface_contact_loops = 0
; support_material_interface_extruder = 1
; support_material_interface_layers = 3
; support_material_interface_pattern = rectilinear
; support_material_interface_spacing = 0
; support_material_interface_speed = 100%
; support_material_pattern = rectilinear
; support_material_solid_first_layer = 0
; support_material_spacing = 2.5
; support_material_speed = 50
; support_material_synchronize_layers = 0
; support_material_threshold = 0
; support_material_with_sheath = 1
; support_material_xy_spacing = 50%
; temperature = 240
; template_custom_gcode = 
; thin_perimeters = 1
; thin_perimeters_all = 0
; thin_walls = 1
; thin_walls_merge = 1
; thin_walls_min_width = 33%
; thin_walls_overlap = 50%
; thin_walls_speed = 60
; threads = 4
; thumbnails = 0x0,0x0
; thumbnails_color = #018aff
; thumbnails_custom_color = 0
; thumbnails_with_bed = 1
; time_estimation_compensation = 100%
; tool_name = ""
; toolchange_gcode = M600
; top_fan_speed = -1
; top_fill_pattern = monotonic
; top_infill_extrusion_width = 0.4
; top_solid_infill_speed = 80%
; top_solid_layers = 4
; top_solid_min_thickness = 0.5
; travel_speed = 100
; use_firmware_retraction = 0
; use_relative_e_distances = 0
; use_volumetric_e = 0
; variable_layer_height = 1
; wipe = 0
; wipe_advanced = 0
; wipe_advanced_algo = linear
; wipe_advanced_multiplier = 60
; wipe_advanced_nozzle_melted_volume = 120
; wipe_extra_perimeter = 0
; wipe_into_infill = 0
; wipe_into_objects = 0
; wipe_tower = 0
; wipe_tower_bridging = 10
; wipe_tower_brim = 150%
; wipe_tower_no_sparse_layers = 0
; wipe_tower_rotation_angle = 0
; wipe_tower_width = 60
; wipe_tower_x = 180
; wipe_tower_y = 140
; wiping_volumes_extruders = 70,70
; wiping_volumes_matrix = 0
; xy_inner_size_compensation = 0
; xy_size_compensation = 0
; z_offset = 0
; z_step = 0.000625
