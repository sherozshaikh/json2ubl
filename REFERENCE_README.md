# PipelineScope

**Production-ready profiling and performance monitoring for Python data pipelines, ML workflows, and ETL systems**

[![PyPI version](https://badge.fury.io/py/pipelinescope.svg)](https://badge.fury.io/py/pipelinescope)
[![Python Versions](https://img.shields.io/pypi/pyversions/pipelinescope.svg)](https://pypi.org/project/pipelinescope/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[PipelineScope](https://pypi.org/project/pipelinescope/) is a lightweight Python profiling library that instruments data pipelines, ETL systems, and ML workflows to identify bottlenecks, track resource consumption, and extrapolate performance metrics across scales.

---

## ✨ Features

- **Zero-Configuration Profiling** - Works out of the box with sensible defaults
- **Scalable Insights** - Sample at 100 functions, extrapolate to 1M+ with statistical confidence
- **Resource Monitoring** - CPU, GPU, and memory tracking with per-function attribution
- **Production Ready** - Minimal overhead, deterministic profiling via `sys.setprofile`
- **Static HTML Reports** - Modern glassmorphism UI, no server dependencies
- **CLI Utilities** - Diff profiling runs, compare baseline vs. current performance
- **YAML Configuration** - Flexible runtime configuration with auto-discovery
- **Comprehensive Logging** - Built on py-logex for structured, production-grade logging
- **Realistic Examples** - Three end-to-end examples: simple linear, nested calls, complex graphs

---

## 📦 Installation

```bash
pip install pipelinescope
```

**Requirements:**
- Python >= 3.8
- psutil >= 5.8.0
- GPUtil >= 1.4.0
- pyyaml >= 6.0
- jinja2 >= 3.0.0
- py-logex-enhanced >= 0.1.3

---

## 🚀 Quickstart

### Minimal Integration (2 Lines)

```python
from pipelinescope import profile_pipeline

if __name__ == "__main__":
    profile_pipeline.start()
    # Your pipeline code here
    process_data()
    train_model()
    export_results()
```

PipelineScope automatically:
1. Profiles all function calls via `sys.setprofile`
2. Monitors CPU, GPU, and memory per function
3. Extrapolates metrics from your sample to expected scale
4. Generates an interactive HTML dashboard
5. Logs detailed profiling data as JSON

**Output**: `.pipelinescope_output/run_<timestamp>/`
- `summary.html` - Interactive profiling dashboard
- `profile_data.json` - Raw profiling data and statistics
- `pipelinescope.log` - Detailed execution logs

---

## 📋 Configuration

Create `.pipelinescope.yaml` in your project root (auto-discovered):

```yaml
# Profiling behavior
sample_size: 100                    # Number of functions sampled
expected_size: 1000000              # Expected function count at production scale
min_time_threshold_ms: 1.0          # Minimum function duration to report (ms)
min_time_percentage: 0.5            # Minimum % of total time to report

# Output
output_dir: .pipelinescope_output
dashboard_title: "My Pipeline"
enable_dashboard: true

# Resource monitoring
enable_cpu_monitoring: true
enable_gpu_monitoring: true

# Filtering
collapse_stdlib: true               # Hide standard library frames
ignore_modules:                     # Exclude module patterns
  - venv
  - site-packages
  - .venv
  - env

# Logging
enable_console_logging: false
log_file: pipelinescope.log
log_level: INFO
```

### Configuration Discovery

If no `config_path` is specified in `profile_pipeline.start()`, PipelineScope walks up 6 directory levels searching for `.pipelinescope.yaml`. Falls back to defaults if not found.

---

## 📊 Architecture Overview

```
User Code
    ↓
PipelineScope.start()
    ↓
┌─────────────────────────────────────────┐
│         Profiler (sys.setprofile)       │
│  ├─ Tracks function calls and timing    │
│  ├─ Manages call stack depth            │
│  └─ Integrates with ResourceMonitor     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│       ResourceMonitor (psutil/GPUtil)   │
│  ├─ Samples CPU % per function          │
│  ├─ Tracks memory (RSS) per function    │
│  └─ Monitors GPU utilization            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│    Stats & Extrapolation Module         │
│  ├─ Aggregates call counts and timing   │
│  ├─ Calculates percentiles              │
│  └─ Extrapolates to production scale    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│     Report Generation (Jinja2)          │
│  ├─ Renders static HTML dashboard       │
│  ├─ Serializes data as JSON             │
│  └─ Writes logs via py-logex            │
└─────────────────────────────────────────┘
    ↓
Output: HTML + JSON + Logs
```

---

## 💻 API Reference

### `profile_pipeline.start(config_path=None)`

Activate profiling for the entire pipeline.

```python
from pipelinescope import profile_pipeline
from pathlib import Path

# Auto-discover config (.pipelinescope.yaml)
profile_pipeline.start()

# Or specify explicit path
profile_pipeline.start(config_path=Path("./config/custom.yaml"))

# Then run your pipeline
my_pipeline()
```

**Behavior:**
- Starts a global singleton profiler (one per process)
- Registers `atexit` handler to finalize on process exit
- Can be called multiple times; subsequent calls are no-ops

### `profile_pipeline.stop()`

Manually finalize profiling and generate outputs. Usually not needed (automatic on process exit).

```python
profile_pipeline.start()
my_pipeline()
profile_pipeline.stop()  # Generate outputs immediately
```

---

## 🔧 End-to-End Usage Example

### Simple Linear Pipeline

```python
# pipeline.py
def extract(data):
    """Load data"""
    return data * 2

def transform(data):
    """Clean and validate"""
    return [x for x in data if x > 0]

def load(data):
    """Save results"""
    return len(data)

def run_pipeline(n):
    data = list(range(n))
    data = extract(data)
    data = transform(data)
    result = load(data)
    return result

# main.py
from pipelinescope import profile_pipeline
from pipeline import run_pipeline

if __name__ == "__main__":
    profile_pipeline.start()
    for i in range(10):
        run_pipeline(1000)
    # Profiling completes automatically on exit
    # Check .pipelinescope_output/run_<timestamp>/ for results
```

**Running:**
```bash
python main.py
# Output:
# PipelineScope profiling started
# Configuration loaded from: defaults
# Tracked 12 functions
# Extrapolating from 100 to 1000000
# Report generated: .pipelinescope_output/run_1704461234/summary.html
# JSON data saved: .pipelinescope_output/run_1704461234/profile_data.json
# PipelineScope profiling complete
```

### Nested Calls (Complex Graph)

See `examples/nested_calls/` for a pipeline with multiple function call layers and interdependencies.

### Complex DAG Pipeline

See `examples/complex_graph/` for a realistic pipeline with parallel-like execution patterns.

---

## 🧪 Testing

### Local Development

```bash
# Clone repository
git clone https://github.com/sherozshaikh/pipelinescope.git
cd pipelinescope

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run test suite
pytest

# Run with coverage report
pytest --cov=pipelinescope --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_profiler.py -v

# Run specific test
pytest tests/test_profiler.py::TestProfilerBasic::test_profiler_start_stop -v
```

### Test Structure

- **Unit Tests**: `test_config.py`, `test_stats.py`, `test_serializer.py`, `test_extrapolation.py`, `test_logger.py`
- **Integration Tests**: `test_profiler.py`, `test_resource_monitor.py`, `test_analyzer.py`, `test_generator.py`
- **E2E Tests**: `test_entrypoint.py` (global profiler lifecycle)
- **CLI Tests**: `test_diff.py` (diff utility)
- **Fixtures**: `conftest.py` (mock psutil/GPUtil, singleton reset, temp directories)

---

## 🔄 CI/CD

This project uses GitHub Actions for continuous testing.

### Local CI Simulation

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests with coverage (as CI does)
pytest --cov=pipelinescope --cov-report=xml --cov-report=term-missing

# Run linting (optional, not in CI)
ruff check src/ tests/
black --check src/ tests/
```

### GitHub Actions Workflow

The repository includes `.github/workflows/tests.yml` which:
- Runs on `push` to `main` and `develop`
- Runs on `pull_request` to `main` and `develop`
- Tests on Python 3.8 (primary)
- Uploads coverage to Codecov
- Uses pip caching for fast builds

---

## 🛠️ Troubleshooting

### No Data Collected

**Issue**: Dashboard is empty or "No profiling data collected" warning.

**Cause**: Pipeline finishes before profiler registers meaningful function calls (e.g., pipeline runs too fast or only calls built-in functions).

**Solution**:
- Ensure your pipeline calls user-defined functions (not just built-ins)
- Profile longer-running pipelines with more function overhead
- Check `min_time_threshold_ms` and `min_time_percentage` config—lower them if needed

### High Overhead / Slow Profiling

**Issue**: Profiler adds significant latency to pipeline execution.

**Cause**: System is profiling too many functions (e.g., stdlib, venv).

**Solution**:
- Set `collapse_stdlib: true` (default)
- Extend `ignore_modules` to exclude unnecessary paths
- Increase `min_time_threshold_ms` to skip short-lived functions

### Missing GPU Data

**Issue**: GPU metrics not appearing in dashboard.

**Cause**: GPUtil not installed, or no NVIDIA GPU detected.

**Solution**:
- Verify GPU driver: `nvidia-smi`
- Set `enable_gpu_monitoring: false` if GPU unavailable
- Check `pipelinescope.log` for GPUtil errors

### Config Not Loading

**Issue**: Custom `.pipelinescope.yaml` ignored; defaults used instead.

**Cause**: Config file path incorrect or not in search path (current directory or 5 parent levels).

**Solution**:
- Verify file exists: `ls -la .pipelinescope.yaml`
- Check YAML syntax: `python -c "import yaml; yaml.safe_load(open('.pipelinescope.yaml'))"`
- Pass explicit path: `profile_pipeline.start(config_path=Path("./config/custom.yaml"))`

### Memory Bloat in Long-Running Pipelines

**Issue**: Memory usage grows unbounded.

**Cause**: Profiler accumulates function stats indefinitely.

**Solution**:
- Profile in segments (restart process between segments)
- Lower `expected_size` to trigger extrapolation earlier
- Review `function_stats` dict size in logs

---

## 📖 Example Outputs

### HTML Dashboard

The generated `summary.html` includes:
- **Function call tree** - Shows nested call hierarchy and timing
- **Top 20 by time** - Slowest functions across the pipeline
- **Resource usage** - CPU, memory, and GPU per function
- **Call statistics** - Counts, percentiles, extrapolated metrics

### JSON Profile Data

`profile_data.json` structure:
```json
{
  "metadata": {
    "sample_size": 100,
    "expected_size": 1000000,
    "profiling_duration_seconds": 12.34,
    "total_functions": 45
  },
  "function_stats": {
    "module:function_name": {
      "call_count": 1000,
      "total_time_ms": 5000.0,
      "cpu_percent": 45.2,
      "memory_mb": 256.5,
      "gpu_memory_mb": 512.0
    }
  },
  "extrapolated_stats": {
    "module:function_name": {
      "extrapolated_call_count": 10000000,
      "extrapolated_total_time_ms": 50000000.0
    }
  }
}
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Run the test suite: `pytest --cov=pipelinescope`
5. Ensure code formatting and linting:
   isort .
   black .
   ruff check --fix .
   ruff format .
6. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [psutil](https://psutil.readthedocs.io/) for system resource monitoring
- GPU tracking via [GPUtil](https://github.com/anderskm/gputil)
- Configuration via [PyYAML](https://pyyaml.org/)
- Templating with [Jinja2](https://jinja.palletsprojects.com/)
- Production logging via [py-logex](https://github.com/sherozshaikh/py-logex)

---

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/sherozshaikh/pipelinescope/issues)
- **PyPI**: [https://pypi.org/project/pipelinescope/](https://pypi.org/project/pipelinescope/)
- **Documentation**: See this README and inline code docstrings

---

Made with ❤️ for production data engineering
