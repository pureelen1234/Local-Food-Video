"""실행기: LFF_SCRIPT 로 지정한 스크립트를 실행하고, 오류가 나면 내용을 창으로 보여 준다.
콘솔(Python)에서:  LFF_SCRIPT='lff_01_build.py'; exec(open(<이 파일 경로>).read())
"""
import traceback
import unreal

_P = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + 'Scripts/LocalFoodFilm/'
_name = globals().get('LFF_SCRIPT', 'lff_01_build.py')
try:
    _g = {'__name__': '__main__', 'LFF_QUALITY': globals().get('LFF_QUALITY', 'preview')}
    exec(compile(open(_P + _name, encoding='utf-8').read(), _P + _name, 'exec'), _g)
except Exception:  # noqa: BLE001
    _tb = traceback.format_exc()
    unreal.log_error(_tb)
    unreal.EditorDialog.show_message('LocalFoodFilm 오류 (%s)' % _name, _tb[-2500:], unreal.AppMsgType.OK)
