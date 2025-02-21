package ltid.log_graph;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.util.Optional;

import ltid.log_graph.commands.Injections;
import ltid.log_graph.commands.OutputGraph;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Model.CommandSpec;
import picocli.CommandLine.Option;
import picocli.CommandLine.Spec;

@Command(name = "ltid_log_graph", mixinStandardHelpOptions = true)
public class Launcher {
    public static void main(String... argv) {
        System.exit(new CommandLine(new Launcher()).execute(argv));
    }

    @Spec
    CommandSpec spec;

    @Option(names = { "-e", "--env",
            "--environment" }, defaultValue = "file:.", converter = Environment.Converter.class)
    Environment env;

    public PrintWriter out() {
        return spec.commandLine().getOut();
    }

    @Command(name = "injections", mixinStandardHelpOptions = true)
    void injections(@Option(names = { "-x", "--ids" }) File ids) throws IOException {
        if (ids != null) {
            var parsed = Files.readAllLines(ids.toPath()).toArray(size -> new String[size]);
            Injections.execute(out(), env, Optional.of(parsed));
        } else {
            Injections.execute(out(), env, Optional.empty());
        }
    }

    @Command(name = "output", mixinStandardHelpOptions = true)
    void output() throws IOException {
        OutputGraph.run(out(), env);
    }
}
