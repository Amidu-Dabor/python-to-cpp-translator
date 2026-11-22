from translator.verify import compare, normalise


def test_timing_lines_and_spacing_are_ignored():
    a = "Total: 10980\nExecution Time: 63.098296 seconds\n"
    b = "Total:   10980\r\nExecution Time: 0.000812 seconds"
    assert normalise(a) == normalise(b) == "Total: 10980"


def test_identical_results_pass():
    assert compare("Total: 10980\n", "Total: 10980\n").match


def test_wrong_result_fails_with_a_diff():
    verdict = compare("Total: 10980", "Total: 0")
    assert not verdict.match
    assert "-Total: 10980" in verdict.diff and "+Total: 0" in verdict.diff


def test_crash_fails_even_if_output_looks_right():
    assert not compare("Total: 1", "Total: 1", returncode=-8).match


def test_empty_output_fails():
    assert not compare("Total: 1", "Execution Time: 0.1 seconds").match
