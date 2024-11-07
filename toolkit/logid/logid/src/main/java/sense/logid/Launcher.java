package sense.logid;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.util.List;
import java.util.Optional;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.ITypeConverter;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;
import picocli.CommandLine.Spec;
import picocli.CommandLine.Model.CommandSpec;

@Command(name = "logid", mixinStandardHelpOptions = true)
class Launcher {
    public static void main(String... argv) {
        System.exit(new CommandLine(new Launcher()).execute(argv));
    }

    @Spec
    CommandSpec spec;

    @Option(names = {"-e", "--env", "--environment"}, defaultValue = "file:.", converter = Environment.Converter.class)
    Environment env;

    public PrintWriter out() {
        return spec.commandLine().getOut();
    }

    @Command(name = "gather", mixinStandardHelpOptions = true)
    void gather() {
        Gather.execute(out(), env.model());
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
}
