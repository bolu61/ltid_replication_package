import java.util.logging.Logger;

public class JavaUtilLogging {
    static Logger logger = Logger.getLogger(JavaUtilLogging.class.getName());

    public static void main(String... args) throws Exception {
        // print hello world
        logger.info("Hello World!");
    }
}
