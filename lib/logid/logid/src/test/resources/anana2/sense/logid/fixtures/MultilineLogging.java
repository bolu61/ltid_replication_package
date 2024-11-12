import java.util.logging.Logger;

public class MultilineLogging {
    static Logger logger = Logger.getLogger(MultilineLogging.class.getName());

    public static void main(String... args) throws Exception {
        // print hello world
        String subject = "pineapple";
        String attribute = "sweet";
        logger.info("{}\n{}",
                attribute,
                subject);
    }
}
