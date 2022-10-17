import java.util.Random;
import java.util.logging.Logger;

public class LogWithID {
    private static Logger logger = Logger.getLogger(LogWithID.class.getName());

    public static void main(String... args) throws Exception {
        Random random = new Random();
        var ida = random.nextInt();
        var idb = random.nextInt();
        var idc = random.nextInt();
        logger.info("first {}", ida);
        while (false) {
            logger.info("second {}", idb);
        }
        logger.info("third {}", idc);
    }
}
