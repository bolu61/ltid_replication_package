package ltid.log_graph;

import java.util.regex.Pattern;

import picocli.CommandLine.ITypeConverter;
import spoon.Launcher;
import spoon.MavenLauncher;
import spoon.compiler.Environment.PRETTY_PRINTING_MODE;
import spoon.reflect.CtModel;
import spoon.reflect.declaration.CtPackage;
import spoon.support.sniper.SniperJavaPrettyPrinter;

public class Environment {

    static class Converter implements ITypeConverter<Environment> {
        private static final Pattern pattern =
                Pattern.compile("(?<scheme>[a-z][a-z0-9]*):(?<paths>.*)");

        @Override
        public Environment convert(String value) throws Exception {
            var uri = pattern.matcher(value);

            if (!uri.matches()) {
                throw new IllegalArgumentException(String.format("invalid model uri %s", value));
            }

            switch (uri.group("scheme")) {
                case "file": {
                    var launcher = new Launcher();
                    for (var path : uri.group("paths").split(";")) {
                        launcher.addInputResource(path);
                    }
                    return new Environment(launcher);
                }
                case "maven": {
                    var launcher = new MavenLauncher(uri.group("paths"), MavenLauncher.SOURCE_TYPE.APP_SOURCE, true);
                    return new Environment(launcher);
                }
                default: {
                    throw new IllegalArgumentException(String.format("invalid launcher %s", value));
                }
            }
        }
    }

    private final Launcher launcher;

    private Environment(Launcher launcher) {
        this.launcher = launcher;
        this.configure();
    }

    private void configure() {
        var env = launcher.getEnvironment();
        env.setComplianceLevel(11);
        env.setIgnoreDuplicateDeclarations(true);
        env.setNoClasspath(true);
        env.setAutoImports(true);
        env.setPrettyPrintingMode(PRETTY_PRINTING_MODE.AUTOIMPORT);
        env.setPrettyPrinterCreator(() -> new SniperJavaPrettyPrinter(env));
    }

    public CtModel model() {
        return launcher.buildModel();
    }
    
    public CtPackage rootPackage() {
        return this.model().getRootPackage();
    }

    public SniperJavaPrettyPrinter sniper() {
        return new SniperJavaPrettyPrinter(launcher.getEnvironment());
    }
}
