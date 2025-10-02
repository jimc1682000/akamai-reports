#!/usr/bin/env python3
"""
Test Runner Script for Akamai Traffic Report System

Provides convenient test execution with coverage reporting and result analysis.
"""

import json
import os
import subprocess
import sys
from datetime import datetime


def run_command(command, description):
    """Run a shell command and return the result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        print(f"✅ {description} - SUCCESS")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return None


def check_dependencies():
    """Check if required test dependencies are installed"""
    print("📋 檢查測試依賴...")

    required_packages = [
        "pytest",
        "pytest-cov",
        "coverage",
        "requests",
        "akamai.edgegrid",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            subprocess.run(
                [sys.executable, "-c", f"import {package.replace('-', '_')}"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ 缺少測試依賴: {', '.join(missing_packages)}")
        print("請執行: pip install -r requirements-test.txt")
        return False

    print("✅ 所有測試依賴已安裝")
    return True


def run_individual_tests():
    """Run individual test modules and collect results"""
    test_modules = [
        "test_config_loader.py",
        "test_time_functions.py",
        "test_utility_functions.py",
        "test_api_functions.py",
        "test_report_functions.py",
        "test_integration.py",
    ]

    results = {}

    for module in test_modules:
        if not os.path.exists(module):
            print(f"⚠️  測試模組不存在: {module}")
            continue

        print(f"\n🧪 執行 {module}...")
        result = run_command(
            f"python -m pytest {module} -v --tb=short", f"執行 {module}"
        )

        if result:
            results[module] = "PASSED"
        else:
            results[module] = "FAILED"

    return results


def run_coverage_tests():
    """Run complete test suite with coverage"""
    print("\n📊 執行完整測試套件 (包含覆蓋率分析)...")

    coverage_command = (
        "python -m pytest "
        "--cov=. "
        "--cov-report=html:htmlcov "
        "--cov-report=term-missing "
        "--cov-report=xml:coverage.xml "
        "--cov-fail-under=90 "
        "-v"
    )

    result = run_command(coverage_command, "完整測試套件執行")
    return result is not None


def analyze_coverage_report():
    """Analyze and display coverage report"""
    coverage_file = "coverage.xml"
    if not os.path.exists(coverage_file):
        print("❌ 找不到覆蓋率報告檔案")
        return

    print("\n📈 分析覆蓋率報告...")

    try:
        # Parse XML coverage report
        import xml.etree.ElementTree as ET

        tree = ET.parse(coverage_file)
        root = tree.getroot()

        # Extract overall coverage
        coverage_attr = root.attrib
        line_rate = float(coverage_attr.get("line-rate", 0)) * 100
        branch_rate = float(coverage_attr.get("branch-rate", 0)) * 100

        print("📊 整體覆蓋率:")
        print(f"   行覆蓋率: {line_rate:.2f}%")
        print(f"   分支覆蓋率: {branch_rate:.2f}%")

        # Extract per-file coverage
        print("\n📁 檔案覆蓋率詳情:")

        packages = root.find("packages")
        if packages:
            for package in packages.findall("package"):
                classes = package.find("classes")
                if classes:
                    for cls in classes.findall("class"):
                        filename = cls.get("filename", "")
                        if filename and not filename.startswith("test_"):
                            file_line_rate = float(cls.get("line-rate", 0)) * 100
                            print(f"   {filename}: {file_line_rate:.1f}%")

        # Coverage status
        if line_rate >= 90:
            print(f"\n✅ 覆蓋率達標 ({line_rate:.1f}% >= 90%)")
            return True
        else:
            print(f"\n⚠️  覆蓋率未達標 ({line_rate:.1f}% < 90%)")
            return False

    except Exception as e:
        print(f"❌ 分析覆蓋率報告時發生錯誤: {e}")
        return False


def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n📝 生成測試報告...")

    report_data = {
        "timestamp": datetime.now().isoformat(),
        "test_environment": {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd(),
        },
        "test_results": {},
        "coverage_info": {},
    }

    # Add coverage info if available
    if os.path.exists("coverage.xml"):
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse("coverage.xml")
            root = tree.getroot()

            report_data["coverage_info"] = {
                "line_rate": float(root.get("line-rate", 0)) * 100,
                "branch_rate": float(root.get("branch-rate", 0)) * 100,
                "lines_covered": root.get("lines-covered", 0),
                "lines_valid": root.get("lines-valid", 0),
            }
        except Exception as e:
            report_data["coverage_info"]["error"] = str(e)

    # Save report
    report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_filename, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"📄 測試報告已保存: {report_filename}")
        return report_filename
    except Exception as e:
        print(f"❌ 保存測試報告失敗: {e}")
        return None


def display_test_summary(individual_results, coverage_success):
    """Display comprehensive test summary"""
    print("\n" + "=" * 80)
    print("📊 測試執行摘要")
    print("=" * 80)

    # Individual test results
    if individual_results:
        print("\n🧪 個別測試模組結果:")
        passed = sum(1 for result in individual_results.values() if result == "PASSED")
        total = len(individual_results)

        for module, result in individual_results.items():
            status_icon = "✅" if result == "PASSED" else "❌"
            print(f"   {status_icon} {module}: {result}")

        print(f"\n   總計: {passed}/{total} 個模組通過")

    # Coverage results
    print("\n📈 覆蓋率結果:")
    if coverage_success:
        print("   ✅ 覆蓋率達標 (≥90%)")
    else:
        print("   ❌ 覆蓋率未達標 (<90%)")

    # Overall status
    overall_success = coverage_success and (
        not individual_results
        or all(r == "PASSED" for r in individual_results.values())
    )

    print("\n🎯 整體測試狀態:")
    if overall_success:
        print("   ✅ 所有測試通過，品質達標")
    else:
        print("   ❌ 存在測試失敗或覆蓋率不足")

    return overall_success


def main():
    """Main test runner function"""
    print("🚀 Akamai Traffic Report 測試執行器")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        return 1

    # Run individual tests
    individual_results = run_individual_tests()

    # Run coverage tests
    coverage_success = run_coverage_tests()

    # Analyze coverage
    if coverage_success:
        coverage_success = analyze_coverage_report()

    # Generate comprehensive report
    generate_test_report()

    # Display summary
    overall_success = display_test_summary(individual_results, coverage_success)

    # Final instructions
    print("\n📋 後續步驟:")
    if os.path.exists("htmlcov/index.html"):
        print("   🔍 查看詳細覆蓋率報告: open htmlcov/index.html")

    if not overall_success:
        print("   🔧 修復測試失敗項目後重新執行")
        return 1

    print("   🎉 所有測試通過，可以進行代碼提交")
    return 0


if __name__ == "__main__":
    sys.exit(main())
