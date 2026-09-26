"""무비 렌더 큐로 30초판 렌더 (맥: Apple ProRes .mov + 음성 .wav).
LFF_QUALITY = 'preview'(1280x720) 또는 'final'(1920x1080).
결과: 프로젝트 폴더 Saved/MovieRenders/
"""
import unreal

Q = globals().get('LFF_QUALITY', 'preview')
W, H = (1920, 1080) if Q == 'final' else (1280, 720)
LEVEL = '/Game/LocalFoodFilm/Maps/LFF_Main30'
SEQ = '/Game/LocalFoodFilm/Sequences/LS_LocalFood30'
OUT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + 'MovieRenders/'

subsys = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
queue = subsys.get_queue()
queue.delete_all_jobs()
job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
job.set_editor_property('job_name', 'LFF30_' + Q)
job.set_editor_property('map', unreal.SoftObjectPath(LEVEL))
job.set_editor_property('sequence', unreal.SoftObjectPath(SEQ))
cfg = job.get_configuration()
out = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
out.set_editor_property('output_resolution', unreal.IntPoint(W, H))
out.set_editor_property('output_directory', unreal.DirectoryPath(OUT))
out.set_editor_property('file_name_format', '{sequence_name}_' + Q)
cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
cfg.find_or_add_setting_by_class(unreal.MoviePipelineAppleProResOutput)
cfg.find_or_add_setting_by_class(unreal.MoviePipelineWaveOutput)
aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
aa.set_editor_property('spatial_sample_count', 1)
aa.set_editor_property('temporal_sample_count', 8 if Q == 'final' else 2)
subsys.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
unreal.log('[LFF] 렌더 시작: %dx%d → %s' % (W, H, OUT))
