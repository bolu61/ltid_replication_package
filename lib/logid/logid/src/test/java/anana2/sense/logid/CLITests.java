package anana2.sense.logid;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.params.provider.Arguments.arguments;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.net.URISyntaxException;
import java.nio.file.Path;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import picocli.CommandLine;
import sense.logid.Launcher;

public class CLITests {

    @ParameterizedTest
    @MethodSource("gathercsv_cases")
    void gathercsv(String env, String expected) {
        var out = new StringWriter();
        var err = assertDoesNotThrow(() -> {
            return new CommandLine(new Launcher())
                    .setOut(new PrintWriter(out))
                    .execute("-e", env, "gather");
        });
        assertAll(
                () -> assertEquals(0, err),
                () -> assertEquals(expected, out.toString()));
    }

    static Arguments[] gathercsv_cases() {
        return new Arguments[] {
                arguments(file("WhileEmptyBody.java"),
                        "\"\",\"0\",\"INFO\",\"sweet pineapple\"\n"),
                arguments(file("JavaUtilLogging.java"),
                        "\"\",\"0\",\"INFO\",\"Hello World!\"\n"),
                arguments(file("MultilineLogging.java"),
                        "\"\",\"0\",\"INFO\",\"{Attribute0}\\n{Subject1}\"\n"),
                arguments(file("LogWithID.java"),
                        "\"\",\"0\",\"INFO\",\"first {Ida0}\"\n\"0\",\"1\",\"INFO\",\"second {Idb0}\"\n\"0\",\"2\",\"INFO\",\"third {Idc0}\"\n"),
                arguments(maven("sample"),
                        "\"\",\"0\",\"INFO\",\"Hello World!\"\n") };
    }

    public static String path(String resource) {
        try {
            var uri = CLITests.class
                    .getResource(String.format("fixtures/%s", resource))
                    .toURI();
            return Path.of(uri).toString();
        } catch (URISyntaxException e) {
            throw new RuntimeException(e);
        }
    }

    public static String file(String resource) {
        return String.format("file:%s", path(resource));
    }

    public static String maven(String resource) {
        return String.format("maven:%s", path(resource));
    }
}
