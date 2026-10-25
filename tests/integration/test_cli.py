import json, os, subprocess, sys

def test_status_uses_configured_store_from_another_cwd(tmp_path):
    data=tmp_path/'data'; env_file=tmp_path/'.env'
    env_file.write_text(f'COLLECTOR_DATA_DIR={data.as_posix()}\nCOLLECTOR_API_URL=http://127.0.0.1:8000\n')
    root=str(__import__('pathlib').Path(__file__).parents[2]); env={**os.environ,'PYTHONPATH':root}
    result=subprocess.run([sys.executable,'-m','collector','--env',str(env_file),'status'],cwd=tmp_path,env=env,capture_output=True,text=True)
    assert result.returncode==0 and json.loads(result.stdout)['data_dir']==str(data)
